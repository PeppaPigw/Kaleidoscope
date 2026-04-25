"""Focused regression tests for previously shipped backend bugs."""

from __future__ import annotations

import asyncio
import io
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from starlette.requests import Request


class FakeScalarResult:
    """Minimal scalar-result double for service and task tests."""

    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row

    def scalars(self):
        return self

    def all(self):
        if isinstance(self._row, list):
            return self._row
        return [self._row] if self._row is not None else []


def _request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request({"type": "http", "headers": raw_headers})


def test_get_current_user_id_requires_auth_when_jwt_secret_is_enabled(monkeypatch):
    from app import auth
    from app.dependencies import get_current_user_id

    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "decode_access_token", lambda token: None)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(_request())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required"

    with pytest.raises(HTTPException) as invalid_exc:
        get_current_user_id(_request({"Authorization": "Bearer invalid-token"}))

    assert invalid_exc.value.status_code == 401
    assert invalid_exc.value.detail == "Invalid or expired token"


def test_get_current_user_id_keeps_single_user_fallback_without_jwt(monkeypatch):
    from app import auth
    from app.dependencies import get_current_user_id
    from app.models.collection import DEFAULT_USER_ID

    monkeypatch.setattr(auth, "JWT_SECRET", "")
    monkeypatch.setattr(auth, "decode_access_token", lambda token: None)

    assert get_current_user_id(_request()) == DEFAULT_USER_ID


def test_quality_service_exposes_score_metadata_alias():
    from app.services.quality_service import QualityService

    paper_id = str(uuid4())
    paper = SimpleNamespace(
        id=paper_id,
        title="Paper",
        abstract="Abstract",
        doi="10.1000/example",
        arxiv_id="2401.12345",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        keywords=["ml"],
        citation_count=1,
        venue_id=uuid4(),
        summary="Summary",
        highlights=["Highlight"],
        contributions=["Contribution"],
        limitations=["Limitation"],
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult(paper)))
    service = QualityService(db)

    async def run_test():
        result = await service.score_metadata(paper_id)
        assert result["paper_id"] == paper_id
        assert result["score_pct"] == 100

    asyncio.run(run_test())


def test_admin_reprocess_queues_ingest_task(monkeypatch):
    from app.services.admin_service import AdminService

    queued_calls: list[tuple[str, str]] = []
    fake_task_module = ModuleType("app.tasks.ingest_tasks")
    fake_task_module.ingest_paper = SimpleNamespace(
        delay=lambda paper_id, id_type: queued_calls.append((paper_id, id_type))
    )
    monkeypatch.setitem(sys.modules, "app.tasks.ingest_tasks", fake_task_module)

    papers = [
        SimpleNamespace(id=uuid4(), doi="10.1000/example"),
        SimpleNamespace(id=uuid4(), doi=None),
    ]
    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult(papers)))
    service = AdminService(db)

    async def run_test():
        result = await service.reprocess_stale_papers(limit=2)
        assert result["queued_count"] == 2
        assert queued_calls == [
            (str(papers[0].id), "doi"),
            (str(papers[1].id), "arxiv"),
        ]

    asyncio.run(run_test())


def test_resolve_papers_by_arxiv_prefers_existing_local_papers():
    from app.api.v1 import papers

    first_id = uuid4()
    second_id = uuid4()
    rows = [
        SimpleNamespace(
            id=first_id,
            arxiv_id="2308.00692",
            ingestion_status="indexed",
            parser_version="mineru",
        ),
        SimpleNamespace(
            id=second_id,
            arxiv_id="2401.12345",
            ingestion_status="parsed",
            parser_version="mineru-pdf",
        ),
    ]
    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult(rows)))

    async def run_test():
        response = await papers.resolve_papers_by_arxiv(
            papers.PaperResolveByArxivRequest(
                arxiv_ids=[
                    "2308.00692",
                    "2308.00692",
                    " ",
                    "2401.12345",
                ]
            ),
            db=db,
        )

        assert response.matches == [
            papers.PaperResolveByArxivItem(
                paper_id=str(first_id),
                arxiv_id="2308.00692",
                ingestion_status="indexed",
            ),
            papers.PaperResolveByArxivItem(
                paper_id=str(second_id),
                arxiv_id="2401.12345",
                ingestion_status="parsed",
            ),
        ]
        assert db.execute.await_count == 1
        statement = db.execute.await_args.args[0]
        compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
        assert "parser_version" in compiled
        assert "mineru-%" in compiled
        assert "ingestion_status" in compiled

    asyncio.run(run_test())


def test_sanitize_mineru_markdown_removes_nul_bytes():
    from app.services.parsing.mineru_service import sanitize_mineru_markdown

    cleaned = sanitize_mineru_markdown("alpha\x00beta\x00gamma")

    assert cleaned == "alphabetagamma"


def test_extract_title_from_mineru_markdown_uses_first_h1():
    from app.services.parsing.mineru_service import extract_title_from_markdown

    markdown = (
        "# LISA: Reasoning Segmentation via Large Language Model\n\n"
        "Authors\n\n"
        "# Abstract\n\n"
        "Abstract text.\n"
    )

    assert (
        extract_title_from_markdown(markdown)
        == "LISA: Reasoning Segmentation via Large Language Model"
    )


def test_extract_title_from_mineru_markdown_skips_generic_section_headings():
    from app.services.parsing.mineru_service import extract_title_from_markdown

    markdown = (
        "Author Line\n\n"
        "# Abstract\n\n"
        "Abstract text.\n\n"
        "# 1. Introduction\n\n"
        "Intro text.\n"
    )

    assert extract_title_from_markdown(markdown) is None


def test_labels_have_any_values_rejects_all_empty_payloads():
    from app.services.analysis.labeling_service import labels_have_any_values

    assert (
        labels_have_any_values(
            {
                "domain": [],
                "task": [],
                "method": [],
                "data_object": [],
                "application": [],
                "meta": {
                    "paper_type": [],
                    "evaluation_quality": [],
                    "resource_constraint": [],
                },
            }
        )
        is False
    )
    assert (
        labels_have_any_values(
            {
                "domain": ["computer vision"],
                "task": [],
                "method": [],
                "data_object": [],
                "application": [],
                "meta": {
                    "paper_type": [],
                    "evaluation_quality": [],
                    "resource_constraint": [],
                },
            }
        )
        is True
    )


def test_deep_analysis_is_valid_rejects_empty_prompt_artifacts():
    from app.services.analysis.paper_analyst import deep_analysis_is_valid

    assert (
        deep_analysis_is_valid(
            {
                "status": "ok",
                "analysis": "[EXT] *Note: As the prompt provided empty fields for the paper's Abstract and Full Text...",
                "fulltext_chars": 0,
            }
        )
        is False
    )
    assert (
        deep_analysis_is_valid(
            {
                "status": "ok",
                "analysis": "Actual analysis body",
                "fulltext_chars": 2048,
            }
        )
        is True
    )


def test_paper_analyst_requires_title_and_text():
    from app.services.analysis.paper_analyst import PaperAnalystService

    paper = SimpleNamespace(
        id=uuid4(),
        title="",
        abstract="",
        full_text_markdown="",
        authors=[],
        raw_metadata={},
        published_at=None,
    )

    async def run_test():
        svc = PaperAnalystService()
        try:
            await svc.analyse(paper)
        finally:
            await svc.close()

    with pytest.raises(ValueError, match="title unavailable"):
        asyncio.run(run_test())


def test_index_paper_broadcasts_alert_matches(monkeypatch):
    from app.tasks import ingest_tasks

    # Patch the module-level logger so log.bind().info() etc. are no-ops
    noop_logger = SimpleNamespace(
        bind=lambda **kw: SimpleNamespace(
            info=lambda *a, **kw: None,
            warning=lambda *a, **kw: None,
            error=lambda *a, **kw: None,
            debug=lambda *a, **kw: None,
        ),
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
        debug=lambda *a, **kw: None,
    )
    monkeypatch.setattr(ingest_tasks, "logger", noop_logger)

    paper_id = str(uuid4())
    paper = SimpleNamespace(
        id=uuid4(),
        title="Indexed Paper",
        abstract="Abstract",
        doi="10.1000/example",
        arxiv_id="2401.12345",
        published_at=None,
        keywords=[],
        authors=[],
        venue=None,
        paper_type=None,
        oa_status=None,
        has_full_text=True,
        citation_count=0,
        ingestion_status="parsed",
        ingestion_error=None,
    )
    alert = SimpleNamespace(id=uuid4(), rule_name="hot papers")
    broadcasts: list[tuple[str, dict]] = []

    session = SimpleNamespace(
        execute=AsyncMock(return_value=FakeScalarResult(paper)),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_session_factory():
        yield session

    monkeypatch.setattr(ingest_tasks, "asyncio", __import__("asyncio"))
    monkeypatch.setitem(
        sys.modules,
        "app.services.search.keyword_search",
        SimpleNamespace(
            KeywordSearchService=lambda: SimpleNamespace(index_paper=lambda doc: None)
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.services.search.vector_search",
        SimpleNamespace(
            VectorSearchService=lambda: SimpleNamespace(
                index_paper=lambda **kwargs: None
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.services.monitoring.alert_service",
        SimpleNamespace(
            AlertService=lambda db, user_id: SimpleNamespace(
                evaluate_rules=AsyncMock(return_value=[alert])
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.services.governance_service",
        SimpleNamespace(
            GovernanceService=lambda db: SimpleNamespace(
                fire_webhooks=AsyncMock(return_value=None)
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.services.collection_service",
        SimpleNamespace(
            CollectionService=lambda db, user_id: SimpleNamespace(
                evaluate_smart_collections=AsyncMock(return_value=[])
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.api.v1.sse",
        SimpleNamespace(
            broadcast_event=lambda event_type, payload: broadcasts.append(
                (event_type, payload)
            )
        ),
    )

    from app import dependencies

    monkeypatch.setattr(dependencies, "async_session_factory", fake_session_factory)

    result = ingest_tasks.index_paper_task.run(paper_id)

    assert result["status"] == "indexed"
    assert (
        "alert.matched",
        {
            "alert_id": str(alert.id),
            "paper_id": paper_id,
            "title": paper.title,
            "rule_name": alert.rule_name,
        },
    ) in broadcasts


def test_acquire_fulltext_prefers_mineru_for_remote_papers(monkeypatch):
    from app.tasks import ingest_tasks

    noop_logger = SimpleNamespace(
        bind=lambda **kw: SimpleNamespace(
            info=lambda *a, **kw: None,
            warning=lambda *a, **kw: None,
            error=lambda *a, **kw: None,
            debug=lambda *a, **kw: None,
        ),
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
        debug=lambda *a, **kw: None,
    )
    monkeypatch.setattr(ingest_tasks, "logger", noop_logger)

    paper_id = str(uuid4())
    paper = SimpleNamespace(
        id=uuid4(),
        remote_urls=[],
        arxiv_id="2401.12345",
        doi=None,
        raw_metadata={},
        pdf_path=None,
        has_full_text=False,
        ingestion_status="discovered",
        ingestion_error=None,
    )
    session = SimpleNamespace(
        execute=AsyncMock(return_value=FakeScalarResult(paper)),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_session_factory():
        yield session

    acq_result = SimpleNamespace(
        success=True,
        storage_path="/tmp/example.pdf",
        content_type="pdf",
        source="arxiv",
        error=None,
    )
    mineru_calls: list[tuple[str, str, bool]] = []
    local_parse_calls: list[tuple[str, str]] = []

    monkeypatch.setitem(
        sys.modules,
        "app.services.ingestion.pdf_downloader",
        SimpleNamespace(
            PDFDownloaderService=lambda arxiv, unpaywall, s2: SimpleNamespace(
                acquire_pdf=AsyncMock(return_value=acq_result)
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.arxiv",
        SimpleNamespace(ArxivClient=lambda: SimpleNamespace(close=AsyncMock())),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.unpaywall",
        SimpleNamespace(
            UnpaywallClient=lambda email=None: SimpleNamespace(close=AsyncMock())
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.semantic_scholar",
        SimpleNamespace(
            SemanticScholarClient=lambda: SimpleNamespace(close=AsyncMock())
        ),
    )

    from app import dependencies

    monkeypatch.setattr(dependencies, "async_session_factory", fake_session_factory)
    monkeypatch.setattr(
        ingest_tasks,
        "parse_via_mineru",
        SimpleNamespace(
            delay=lambda pid, url, is_html=False: mineru_calls.append(
                (pid, url, is_html)
            )
        ),
    )
    monkeypatch.setattr(
        ingest_tasks,
        "parse_fulltext_task",
        SimpleNamespace(
            delay=lambda pid, content_type: local_parse_calls.append(
                (pid, content_type)
            )
        ),
    )
    monkeypatch.setattr(
        ingest_tasks,
        "index_paper_task",
        SimpleNamespace(delay=lambda pid: None),
    )

    result = ingest_tasks.acquire_fulltext.run(paper_id)

    assert result["status"] == "acquired"
    assert mineru_calls == [(paper_id, "https://arxiv.org/pdf/2401.12345.pdf", False)]
    assert local_parse_calls == []


def test_acquire_fulltext_uses_local_parser_when_no_mineru_url_exists(monkeypatch):
    from app.tasks import ingest_tasks

    noop_logger = SimpleNamespace(
        bind=lambda **kw: SimpleNamespace(
            info=lambda *a, **kw: None,
            warning=lambda *a, **kw: None,
            error=lambda *a, **kw: None,
            debug=lambda *a, **kw: None,
        ),
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
        debug=lambda *a, **kw: None,
    )
    monkeypatch.setattr(ingest_tasks, "logger", noop_logger)

    paper_id = str(uuid4())
    paper = SimpleNamespace(
        id=uuid4(),
        remote_urls=[],
        arxiv_id=None,
        doi=None,
        raw_metadata={},
        pdf_path=None,
        has_full_text=False,
        ingestion_status="discovered",
        ingestion_error=None,
    )
    session = SimpleNamespace(
        execute=AsyncMock(return_value=FakeScalarResult(paper)),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def fake_session_factory():
        yield session

    acq_result = SimpleNamespace(
        success=True,
        storage_path="/tmp/example.pdf",
        content_type="pdf",
        source="upload",
        error=None,
    )
    mineru_calls: list[tuple[str, str, bool]] = []
    local_parse_calls: list[tuple[str, str]] = []

    monkeypatch.setitem(
        sys.modules,
        "app.services.ingestion.pdf_downloader",
        SimpleNamespace(
            PDFDownloaderService=lambda arxiv, unpaywall, s2: SimpleNamespace(
                acquire_pdf=AsyncMock(return_value=acq_result)
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.arxiv",
        SimpleNamespace(ArxivClient=lambda: SimpleNamespace(close=AsyncMock())),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.unpaywall",
        SimpleNamespace(
            UnpaywallClient=lambda email=None: SimpleNamespace(close=AsyncMock())
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.clients.semantic_scholar",
        SimpleNamespace(
            SemanticScholarClient=lambda: SimpleNamespace(close=AsyncMock())
        ),
    )

    from app import dependencies

    monkeypatch.setattr(dependencies, "async_session_factory", fake_session_factory)
    monkeypatch.setattr(
        ingest_tasks,
        "parse_via_mineru",
        SimpleNamespace(
            delay=lambda pid, url, is_html=False: mineru_calls.append(
                (pid, url, is_html)
            )
        ),
    )
    monkeypatch.setattr(
        ingest_tasks,
        "parse_fulltext_task",
        SimpleNamespace(
            delay=lambda pid, content_type: local_parse_calls.append(
                (pid, content_type)
            )
        ),
    )
    monkeypatch.setattr(
        ingest_tasks,
        "index_paper_task",
        SimpleNamespace(delay=lambda pid: None),
    )

    result = ingest_tasks.acquire_fulltext.run(paper_id)

    assert result["status"] == "acquired"
    assert mineru_calls == []
    assert local_parse_calls == [(paper_id, "pdf")]


def test_celery_worker_declares_all_ingestion_queues():
    from app.worker import CELERY_QUEUE_NAMES, celery_app

    configured_queue_names = {queue.name for queue in celery_app.conf.task_queues}

    assert configured_queue_names == set(CELERY_QUEUE_NAMES)
    assert celery_app.conf.task_default_queue == "celery"
    assert (
        celery_app.conf.task_routes["app.tasks.ingest_tasks.ingest_paper"]["queue"]
        == "ingestion"
    )
    assert (
        celery_app.conf.task_routes["app.tasks.ingest_tasks.parse_via_mineru"]["queue"]
        == "parsing"
    )
    assert (
        celery_app.conf.task_routes["app.tasks.ingest_tasks.index_paper_task"]["queue"]
        == "indexing"
    )


def test_import_single_pdf_publishes_public_url_for_mineru(monkeypatch):
    from app.services.ingestion.pdf_batch_importer import PDFBatchImporter

    added: list[SimpleNamespace] = []

    async def fake_flush():
        for obj in added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    db = SimpleNamespace(
        add=lambda obj: added.append(obj),
        flush=AsyncMock(side_effect=fake_flush),
    )
    importer = PDFBatchImporter(db)

    monkeypatch.setattr(importer, "_find_by_hash", AsyncMock(return_value=None))
    monkeypatch.setattr(
        importer,
        "_store_pdf",
        AsyncMock(return_value="papers/test-paper/local_upload.pdf"),
    )
    monkeypatch.setattr(
        importer,
        "_publish_pdf_for_mineru",
        AsyncMock(return_value="https://bucket.example/Kaleidoscope/source.pdf"),
    )

    async def run_test():
        result = await importer.import_single_pdf(
            filename="local-paper.pdf",
            content=b"%PDF-1.7 mock",
            user_id="user-123",
        )

        paper = added[0]
        assert result["status"] == "imported"
        assert (
            result["mineru_url"]
            == "https://bucket.example/Kaleidoscope/source.pdf"
        )
        assert paper.pdf_path == "papers/test-paper/local_upload.pdf"
        assert paper.remote_urls == [
            {
                "url": "https://bucket.example/Kaleidoscope/source.pdf",
                "source": "local_upload_public",
                "type": "pdf",
            }
        ]
        assert paper.raw_metadata["mineru_source"] == "oss_public_pdf"
        assert (
            paper.raw_metadata["mineru_source_url"]
            == "https://bucket.example/Kaleidoscope/source.pdf"
        )

    asyncio.run(run_test())


def test_upload_single_pdf_queues_mineru_parse(monkeypatch):
    from app.api.v1 import local_pdf

    queued_calls: list[tuple[str, str, bool]] = []
    fake_task_module = ModuleType("app.tasks.ingest_tasks")
    fake_task_module.parse_via_mineru = SimpleNamespace(
        delay=lambda paper_id, url, is_html=False: queued_calls.append(
            (paper_id, url, is_html)
        )
    )
    monkeypatch.setitem(sys.modules, "app.tasks.ingest_tasks", fake_task_module)

    class FakeImporter:
        def __init__(self, db):
            self.db = db

        async def import_single_pdf(self, filename: str, content: bytes, user_id: str):
            assert filename == "paper.pdf"
            assert content == b"%PDF-1.7 mock"
            assert user_id == "user-123"
            return {
                "paper_id": "paper-1",
                "status": "imported",
                "mineru_url": "https://bucket.example/paper-1.pdf",
            }

    monkeypatch.setattr(local_pdf, "PDFBatchImporter", FakeImporter)

    db = SimpleNamespace(commit=AsyncMock())
    file = UploadFile(filename="paper.pdf", file=io.BytesIO(b"%PDF-1.7 mock"))

    async def run_test():
        result = await local_pdf.upload_single_pdf(
            file=file,
            db=db,
            user_id="user-123",
        )

        assert result["paper_id"] == "paper-1"
        db.commit.assert_awaited_once()
        assert queued_calls == [
            ("paper-1", "https://bucket.example/paper-1.pdf", False)
        ]

    asyncio.run(run_test())


def test_batch_upload_pdfs_queues_mineru_parse(monkeypatch):
    from app.api.v1 import local_pdf

    queued_calls: list[tuple[str, str, bool]] = []
    fake_task_module = ModuleType("app.tasks.ingest_tasks")
    fake_task_module.parse_via_mineru = SimpleNamespace(
        delay=lambda paper_id, url, is_html=False: queued_calls.append(
            (paper_id, url, is_html)
        )
    )
    monkeypatch.setitem(sys.modules, "app.tasks.ingest_tasks", fake_task_module)

    class FakeImporter:
        def __init__(self, db):
            self.db = db

        async def import_zip(self, zip_content: bytes, user_id: str):
            assert zip_content == b"mock-zip"
            assert user_id == "user-123"
            return {
                "total": 3,
                "imported": 2,
                "duplicates": 1,
                "errors": 0,
                "results": [
                    {
                        "paper_id": "paper-1",
                        "status": "imported",
                        "mineru_url": "https://bucket.example/paper-1.pdf",
                    },
                    {
                        "paper_id": "paper-2",
                        "status": "duplicate",
                    },
                    {
                        "paper_id": "paper-3",
                        "status": "imported",
                        "mineru_url": "https://bucket.example/paper-3.pdf",
                    },
                ],
                "error_details": [],
            }

    monkeypatch.setattr(local_pdf, "PDFBatchImporter", FakeImporter)

    db = SimpleNamespace(commit=AsyncMock())
    file = UploadFile(filename="papers.zip", file=io.BytesIO(b"mock-zip"))

    async def run_test():
        result = await local_pdf.batch_upload_pdfs(
            file=file,
            db=db,
            user_id="user-123",
        )

        assert result["imported"] == 2
        db.commit.assert_awaited_once()
        assert queued_calls == [
            ("paper-1", "https://bucket.example/paper-1.pdf", False),
            ("paper-3", "https://bucket.example/paper-3.pdf", False),
        ]

    asyncio.run(run_test())

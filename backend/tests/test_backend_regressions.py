"""Focused regression tests for previously shipped backend bugs."""

from __future__ import annotations

import asyncio
import io
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
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
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
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
                "analysis": (
                    "[EXT] *Note: As the prompt provided empty fields for "
                    "the paper's Abstract and Full Text..."
                ),
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


def test_agent_manifest_exposes_tool_contracts():
    from app.services.agent.manifest import build_agent_manifest
    from app.services.agent.tool_dispatcher import TOOLS

    manifest = build_agent_manifest()
    tools = {tool["name"]: tool for tool in manifest["tools"]}

    assert manifest["schema_version"] == "1.0.0"
    assert manifest["service"]["base_path"] == "/api/v1"
    assert manifest["transports"]["rest"]["endpoints"]["context_pack"] == (
        "/api/v1/agent/context-pack"
    )
    assert manifest["transports"]["rest"]["endpoints"]["call_tool"] == (
        "/api/v1/agent/call"
    )
    assert manifest["transports"]["rest"]["endpoints"]["evidence_search"] == (
        "/api/v1/evidence/search"
    )
    assert manifest["transports"]["rest"]["endpoints"]["claim_verify"] == (
        "/api/v1/claims/verify"
    )
    assert set(tools) == {tool["name"] for tool in TOOLS}

    search_tool = tools["search_papers"]
    assert search_tool["id"] == "kaleidoscope.search_papers"
    assert search_tool["input_schema"]["required"] == ["query"]
    assert search_tool["output_schema"]["type"] == "object"
    assert "papers:read" in search_tool["scopes"]
    assert search_tool["cost"] == {"tier": "low", "units": 2}
    assert search_tool["examples"][0]["arguments"]["mode"] == "hybrid"

    assert manifest["external_integrations"]["deepxiv"]["base_path"] == (
        "/api/v1/deepxiv"
    )


def test_paper_resolver_returns_local_doi_match():
    from app.services.paper_resolver_service import PaperResolverService

    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Resolved Paper",
        doi="10.1000/example",
        arxiv_id=None,
        pmid=None,
        openalex_id="W123",
        semantic_scholar_id="abc123",
        ingestion_status="indexed",
        has_full_text=True,
        published_at=None,
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult([paper])))
    service = PaperResolverService(db)

    async def run_test():
        result = await service.resolve(
            "https://doi.org/10.1000/EXAMPLE",
            include_external=False,
        )
        assert result["query"]["identifier_type"] == "doi"
        assert result["query"]["canonical"] == "10.1000/example"
        assert result["local"]["matched"] is True
        assert result["local"]["paper"]["paper_id"] == str(paper_id)
        assert result["import_status"] == {
            "state": "existing",
            "paper_id": str(paper_id),
            "ingestion_status": "indexed",
        }
        assert result["recommended_action"] == "open_local"
        assert result["external_candidates"] == []

    asyncio.run(run_test())


def test_paper_resolver_returns_external_arxiv_candidate():
    from app.services.paper_resolver_service import PaperResolverService

    class FakeOpenAlexClient:
        async def close(self):
            return None

    class FakeSemanticScholarClient:
        async def get_paper(self, paper_id: str):
            assert paper_id == "arXiv:2401.12345"
            return {
                "paperId": "s2-paper",
                "title": "External Paper",
                "externalIds": {"ArXiv": "2401.12345", "DOI": "10.1000/ext"},
                "year": 2024,
                "citationCount": 7,
            }

        async def close(self):
            return None

    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult([])))
    service = PaperResolverService(
        db,
        openalex_client=FakeOpenAlexClient(),
        semantic_scholar_client=FakeSemanticScholarClient(),
    )

    async def run_test():
        result = await service.resolve("arXiv:2401.12345", include_external=True)
        assert result["local"]["matched"] is False
        assert result["external_candidates"] == [
            {
                "source": "semantic_scholar",
                "external_id": "s2-paper",
                "title": "External Paper",
                "doi": "10.1000/ext",
                "arxiv_id": "2401.12345",
                "pmid": None,
                "pmcid": None,
                "url": "https://www.semanticscholar.org/paper/s2-paper",
                "year": 2024,
                "citation_count": 7,
                "match_type": "arxiv",
                "confidence": 0.9,
            }
        ]
        assert result["import_status"] == {"state": "ready_to_import"}
        assert result["recommended_action"] == "import"

    asyncio.run(run_test())


def test_job_service_formats_success_result(monkeypatch):
    from app.services import job_service
    from app.services.job_service import JobService

    class FakeResult:
        id = "job-1"
        state = "SUCCESS"
        result = {"paper_id": "paper-1"}
        info = None
        traceback = None

        def ready(self):
            return True

        def successful(self):
            return True

    monkeypatch.setattr(job_service.celery_app, "AsyncResult", lambda job_id: FakeResult())

    assert JobService().get_job("job-1") == {
        "job_id": "job-1",
        "state": "SUCCESS",
        "status": "succeeded",
        "ready": True,
        "successful": True,
        "failed": False,
        "terminal": True,
        "result": {"paper_id": "paper-1"},
        "error": None,
        "metadata": None,
    }


def test_job_service_cancel_revokes_task(monkeypatch):
    from app.services import job_service
    from app.services.job_service import JobService

    revoked: list[tuple[str, bool, str]] = []

    class FakeControl:
        @staticmethod
        def revoke(job_id: str, terminate: bool = False, signal: str = "SIGTERM"):
            revoked.append((job_id, terminate, signal))

    class FakeResult:
        id = "job-2"
        state = "REVOKED"
        result = None
        info = "revoked"
        traceback = None

        def ready(self):
            return True

        def successful(self):
            return False

    monkeypatch.setattr(job_service.celery_app, "control", FakeControl())
    monkeypatch.setattr(job_service.celery_app, "AsyncResult", lambda job_id: FakeResult())

    result = JobService().cancel_job("job-2", terminate=True, signal="SIGKILL")

    assert revoked == [("job-2", True, "SIGKILL")]
    assert result["state"] == "REVOKED"
    assert result["status"] == "cancelled"
    assert result["cancel_requested"] is True
    assert result["terminate_requested"] is True


def test_job_service_lists_entity_jobs_with_tracking_warning():
    from app.services.job_service import JobService

    assert JobService().list_jobs(entity_id="paper-1") == {
        "entity_id": "paper-1",
        "jobs": [],
        "total": 0,
        "tracking": "celery_result_backend_only",
        "warning": "No durable entity-to-job index is available yet.",
    }


def test_agent_context_pack_builds_compressed_cited_json():
    from app.services.agent.context_pack import AgentContextPackService

    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Context Paper",
        doi="10.1000/context",
        arxiv_id="2401.00001",
        pmid=None,
        openalex_id="W123",
        semantic_scholar_id="s2-123",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
        raw_metadata={"venue": "TestConf", "pdf_url": "https://example.org/p.pdf"},
        abstract="A" * 1200,
        summary="Short summary",
        contributions=["Contribution one", "Contribution two"],
        limitations=["Limitation one"],
        deep_analysis={"analysis": "Detailed analysis"},
        keywords=["rag", "agents"],
        ingestion_status="indexed",
        has_full_text=True,
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult([paper])))
    service = AgentContextPackService(db)

    async def run_test():
        result = await service.build_context_pack(
            paper_ids=[str(paper_id)],
            question="What does the paper contribute?",
            token_budget=800,
            include_evidence=False,
        )
        assert result["scope"]["paper_ids"] == [str(paper_id)]
        assert result["citations"] == [{"key": "P1", "paper_id": str(paper_id)}]
        assert result["papers"][0]["citation_key"] == "P1"
        assert result["papers"][0]["title"] == "Context Paper"
        assert result["papers"][0]["identifiers"]["doi"] == "10.1000/context"
        assert result["papers"][0]["links"]["doi"] == "https://doi.org/10.1000/context"
        assert result["papers"][0]["links"]["pdf"] == "https://example.org/p.pdf"
        assert result["papers"][0]["abstract"].endswith("…")
        assert result["evidence"] == []
        assert result["budget"]["requested_tokens"] == 800

    asyncio.run(run_test())


def test_agent_context_pack_empty_scope_returns_warning():
    from app.services.agent.context_pack import AgentContextPackService

    db = SimpleNamespace(execute=AsyncMock(return_value=FakeScalarResult([])))
    service = AgentContextPackService(db)

    async def run_test():
        result = await service.build_context_pack(paper_ids=[], include_evidence=False)
        assert result["papers"] == []
        assert result["evidence"] == []
        assert result["warnings"] == ["No papers resolved for context pack."]

    asyncio.run(run_test())


def test_grounded_answer_service_builds_cited_answer():
    from app.services.answers.grounded_answer_service import GroundedAnswerService

    result = GroundedAnswerService().build_answer(
        question="What datasets are used?",
        evidence=[
            {
                "id": "chunk-1",
                "paper_id": "paper-1",
                "paper_title": "Dataset Paper",
                "section_title": "Experiments",
                "content": "The evaluation uses CIFAR-10 and ImageNet. Accuracy is reported.",
                "score": 0.91,
                "source": "local_chunk",
            },
            {
                "id": "chunk-2",
                "paper_id": "paper-2",
                "paper_title": "Benchmark Paper",
                "section_title": "Results",
                "content": "The benchmark includes COCO for detection and segmentation tasks.",
                "score": 0.84,
                "source": "local_chunk",
            },
        ],
    )

    assert "[E1]" in result["answer"]
    assert "[E2]" in result["answer"]
    assert result["citations"][0]["anchor"] == "E1"
    assert result["citations"][0]["paper_title"] == "Dataset Paper"
    assert result["diagnostics"]["grounded"] is True
    assert result["diagnostics"]["source_count"] == 2
    assert result["warnings"] == []


def test_grounded_answer_service_reports_missing_evidence():
    from app.services.answers.grounded_answer_service import GroundedAnswerService

    result = GroundedAnswerService().build_answer(
        question="What datasets are used?",
        evidence=[],
    )

    assert result["answer"] == "This cannot be answered from the provided evidence."
    assert result["diagnostics"]["grounded"] is False
    assert result["warnings"] == ["No evidence sources were provided."]


def test_api_key_service_creates_hashed_key(monkeypatch):
    from app.services.api_key_service import APIKeyService

    added: list[object] = []

    class FakeDB:
        def add(self, obj):
            added.append(obj)

        async def flush(self):
            added[0].id = uuid4()
            added[0].created_at = datetime(2026, 4, 25, tzinfo=UTC)
            added[0].updated_at = None
            added[0].last_used_at = None
            added[0].revoked_at = None

    monkeypatch.setattr(
        APIKeyService, "_generate_key", staticmethod(lambda: "ks_live_test-secret")
    )

    async def run_test():
        result = await APIKeyService(FakeDB(), "user-1").create_key(
            name="Agent Key",
            scopes=["papers:read", "rag:ask", "papers:read"],
            description="For tests",
        )
        assert result["key"] == "ks_live_test-secret"
        assert result["key_prefix"] == "ks_live_test-sec"
        assert result["scopes"] == ["papers:read", "rag:ask"]
        assert result["description"] == "For tests"
        assert added[0].key_hash == APIKeyService.hash_key("ks_live_test-secret")
        assert added[0].key_hash != "ks_live_test-secret"

    asyncio.run(run_test())


def test_api_key_service_rejects_invalid_scope():
    from app.services.api_key_service import APIKeyService

    with pytest.raises(ValueError, match="Invalid API key scopes: bad:scope"):
        APIKeyService._normalize_scopes(["papers:read", "bad:scope"])


def test_api_key_service_lists_and_revokes_without_raw_secret():
    from app.services.api_key_service import APIKeyService

    key_id = uuid4()
    key = SimpleNamespace(
        id=key_id,
        name="Agent Key",
        key_prefix="ks_live_test-sec",
        scopes=["papers:read"],
        description=None,
        created_at=datetime(2026, 4, 25, tzinfo=UTC),
        updated_at=None,
        expires_at=None,
        last_used_at=None,
        revoked_at=None,
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=FakeScalarResult(key)),
        flush=AsyncMock(),
    )

    async def run_test():
        listed = await APIKeyService(db, "user-1").list_keys()
        assert listed == [
            {
                "id": str(key_id),
                "name": "Agent Key",
                "key_prefix": "ks_live_test-sec",
                "scopes": ["papers:read"],
                "description": None,
                "created_at": "2026-04-25T00:00:00+00:00",
                "updated_at": None,
                "expires_at": None,
                "last_used_at": None,
                "revoked_at": None,
            }
        ]
        assert "key" not in listed[0]

        revoked = await APIKeyService(db, "user-1").revoke_key(str(key_id))
        assert revoked is not None
        assert revoked["revoked_at"] is not None
        db.flush.assert_awaited_once()

    asyncio.run(run_test())


def test_batch_service_executes_ordered_grounded_answer_and_errors():
    from app.services.batch_service import BatchService

    service = BatchService(db=SimpleNamespace(), user_id="user-1")

    async def run_test():
        result = await service.execute(
            [
                {
                    "id": "answer",
                    "operation": "grounded_answer",
                    "arguments": {
                        "question": "What dataset?",
                        "evidence": [
                            {
                                "id": "chunk-1",
                                "content": "The method is evaluated on ImageNet.",
                                "paper_title": "Vision Paper",
                            }
                        ],
                    },
                },
                {"id": "bad", "operation": "unknown", "arguments": {}},
            ]
        )
        assert result["total"] == 2
        assert result["results"][0]["id"] == "answer"
        assert result["results"][0]["ok"] is True
        assert "[E1]" in result["results"][0]["result"]["answer"]
        assert result["results"][1] == {
            "id": "bad",
            "operation": "unknown",
            "ok": False,
            "error": "Unsupported batch operation: unknown",
        }

    asyncio.run(run_test())


def test_batch_service_rejects_non_object_arguments():
    from app.services.batch_service import BatchService

    async def run_test():
        result = await BatchService(SimpleNamespace(), "user-1").execute(
            [{"id": "bad-args", "operation": "grounded_answer", "arguments": []}]
        )
        assert result == {
            "results": [
                {
                    "id": "bad-args",
                    "operation": "grounded_answer",
                    "ok": False,
                    "error": "arguments must be an object",
                }
            ],
            "total": 1,
        }

    asyncio.run(run_test())


def test_agent_information_classifies_citation_intent():
    from app.services.agent_information_service import AgentInformationService

    result = AgentInformationService.classify_citation_intent(
        "We compare against this baseline and report stronger benchmark scores."
    )

    assert result["label"] == "comparison"
    assert result["confidence"] > 0
    assert result["scores"]["comparison"] > result["scores"]["background"]


def test_agent_information_extracts_benchmark_record():
    from app.services.agent_information_service import AgentInformationService

    record = AgentInformationService.extract_benchmark_record(
        {
            "paper_id": "paper-1",
            "paper_title": "Benchmark Paper",
            "text": (
                "The ResNet baseline is evaluated on ImageNet with accuracy "
                "of 83.4% using A100 GPU hardware."
            ),
        }
    )

    assert record["signals_found"] is True
    assert record["datasets"] == ["ImageNet"]
    assert "accuracy" in record["metrics"]
    assert "A100" in record["hardware"]
    assert record["result_values"][0]["value"] == 83.4


def test_agent_information_extracts_code_and_data_assets():
    from app.services.agent_information_service import AgentInformationService

    paper = SimpleNamespace(
        id=uuid4(),
        title="Artifact Paper",
        abstract="",
        summary="",
        highlights=[],
        contributions=[],
        limitations=[],
        parsed_sections=None,
        full_text_markdown=(
            "Code is available at https://github.com/example/project and data "
            "at https://zenodo.org/records/123."
        ),
        paper_links={
            "status": "ok",
            "code_url": "https://github.com/example/project",
            "dataset_urls": ["https://zenodo.org/records/123"],
            "project_page_url": "https://example.org/project",
        },
    )

    assets = AgentInformationService(SimpleNamespace())._code_and_data_assets(paper)

    assert assets["code_urls"] == ["https://github.com/example/project"]
    assert assets["dataset_urls"] == ["https://zenodo.org/records/123"]
    assert assets["project_page_url"] == "https://example.org/project"


def test_agent_service_routes_are_registered():
    from app.main import create_app

    app = create_app()
    routes = {route.path for route in app.routes}

    expected = {
        "/api/v1/evidence/search",
        "/api/v1/evidence/packs",
        "/api/v1/claims/verify",
        "/api/v1/benchmarks/extract",
        "/api/v1/discovery/delta",
        "/api/v1/exports/jsonl",
        "/api/v1/search/federated",
        "/api/v1/writing/citation-check",
    }
    assert expected <= routes


def test_get_current_user_id_prefers_api_key_middleware_state(monkeypatch):
    from app import auth
    from app.dependencies import get_current_user_id

    request = _request()
    request.state.user_id = "api-user-1"
    monkeypatch.setattr(auth, "JWT_SECRET", "configured-secret")

    assert get_current_user_id(request) == "api-user-1"


def test_external_api_requires_api_key_header():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "API_KEY_REQUIRED"


def test_external_api_accepts_default_api_key_header():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "sk-kaleidoscope"},
        )

    assert response.status_code == 200
    assert response.headers["X-API-Key-Scopes"] == "*"
    assert response.json()["user_id"]


def test_openapi_schema_requires_api_key_header():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        missing = client.get("/api/openapi.json")
        keyed = client.get(
            "/api/openapi.json",
            headers={"X-API-Key": "sk-kaleidoscope"},
        )

    assert missing.status_code == 401
    assert missing.json()["code"] == "API_KEY_REQUIRED"
    assert keyed.status_code == 200
    assert keyed.json()["components"]["securitySchemes"]["ApiKeyHeader"]


def test_external_api_rejects_invalid_api_key_header():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "sk-wrong"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_API_KEY"


def test_openalex_dependency_error_is_handled_4xx():
    import httpx

    from app.api.v1.openalex import _openalex_dependency_error

    exc = _openalex_dependency_error(httpx.TimeoutException("upstream timeout"))

    assert exc.status_code == 424
    assert exc.detail["code"] == "OPENALEX_REQUEST_FAILED"

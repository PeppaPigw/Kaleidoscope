"""Focused regression tests for previously shipped backend bugs."""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
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
        SimpleNamespace(KeywordSearchService=lambda: SimpleNamespace(index_paper=lambda doc: None)),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.services.search.vector_search",
        SimpleNamespace(VectorSearchService=lambda: SimpleNamespace(index_paper=lambda **kwargs: None)),
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
            GovernanceService=lambda db: SimpleNamespace(fire_webhooks=AsyncMock(return_value=None))
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
        SimpleNamespace(broadcast_event=lambda event_type, payload: broadcasts.append((event_type, payload))),
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

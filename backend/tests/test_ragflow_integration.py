"""Integration tests for the Phase 5a RAGFlow sidecar backend surface."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_ragflow_client_create_dataset():
    """RagflowClient should POST dataset creation requests and return decoded data."""
    from app.services.ragflow.ragflow_client import RagflowClient

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/datasets"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = await request.aread()
        assert b'"name":"papers"' in payload
        return httpx.Response(
            status_code=200,
            json={"data": {"id": "ds_123", "name": "papers"}},
            request=request,
        )

    client = RagflowClient(
        api_url="http://ragflow.local",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.create_dataset(
        name="papers",
        embedding_model="bge-large",
        chunk_method="markdown",
    )

    assert result == {"id": "ds_123", "name": "papers"}


@pytest.mark.asyncio
async def test_ragflow_client_health_returns_dict():
    """RagflowClient.health should surface the decoded health payload."""
    from app.services.ragflow.ragflow_client import RagflowClient

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/health"
        return httpx.Response(
            status_code=200,
            json={"status": "ok", "service": "ragflow"},
            request=request,
        )

    client = RagflowClient(
        api_url="http://ragflow.local",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.health()

    assert result == {"status": "ok", "service": "ragflow"}


@pytest.mark.asyncio
async def test_document_sync_disabled_returns_early(monkeypatch: pytest.MonkeyPatch):
    """Document sync should short-circuit without calling RAGFlow when disabled."""
    from app.services.ragflow.document_sync_service import DocumentSyncService

    ragflow_client = MagicMock()
    ragflow_client.upload_document = AsyncMock()

    monkeypatch.setattr(
        "app.services.ragflow.document_sync_service.settings.ragflow_sync_enabled",
        False,
    )

    service = DocumentSyncService(db=MagicMock(), ragflow_client=ragflow_client)

    result = await service.sync_paper(str(uuid4()))

    assert result["enabled"] is False
    assert result["status"] == "disabled"
    ragflow_client.upload_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_workspace_ask_disabled_uses_local_rag(monkeypatch: pytest.MonkeyPatch):
    """Workspace ask should use local embeddings when the RAGFlow flag is off."""
    from app.config import settings
    from app.dependencies import get_db
    from app.main import app
    from app.models.collection import DEFAULT_USER_ID

    collection_id = uuid4()
    calls: dict[str, object] = {}

    mock_collection_result = MagicMock()
    mock_collection_result.scalar_one_or_none.return_value = SimpleNamespace(
        id=collection_id,
        name="Workspace",
        deleted_at=None,
        user_id=DEFAULT_USER_ID,
    )

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_collection_result)

    async def mock_db():
        yield db

    class FakeLocalRAGService:
        def __init__(self, service_db, user_id: str):
            calls["db"] = service_db
            calls["user_id"] = user_id

        async def ask_collection(
            self,
            service_collection_id: str,
            question: str,
            top_k: int = 10,
        ) -> dict[str, object]:
            calls["ask"] = (service_collection_id, question, top_k)
            return {
                "answer": "local answer",
                "sources": [{"paper_id": "paper-1"}],
                "chunks_found": 1,
            }

    app.dependency_overrides[get_db] = mock_db
    monkeypatch.setattr("app.api.v1.ragflow.LocalRAGService", FakeLocalRAGService)

    original_enabled = settings.ragflow_sync_enabled
    settings.ragflow_sync_enabled = False
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/workspaces/{collection_id}/ask",
                json={"question": "What changed?", "top_k": 10},
            )
    finally:
        settings.ragflow_sync_enabled = original_enabled
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["backend"] == "local"
    assert payload["answer"] == "local answer"
    assert payload["sources"] == [{"paper_id": "paper-1"}]
    assert calls == {
        "db": db,
        "user_id": DEFAULT_USER_ID,
        "ask": (str(collection_id), "What changed?", 10),
    }
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_workspace_evidence_disabled_uses_local_rag(
    monkeypatch: pytest.MonkeyPatch,
):
    """Workspace evidence should use local retrieval when the RAGFlow flag is off."""
    from app.config import settings
    from app.dependencies import get_db
    from app.main import app
    from app.models.collection import DEFAULT_USER_ID

    collection_id = uuid4()
    calls: dict[str, object] = {}

    mock_collection_result = MagicMock()
    mock_collection_result.scalar_one_or_none.return_value = SimpleNamespace(
        id=collection_id,
        name="Workspace",
        deleted_at=None,
        user_id=DEFAULT_USER_ID,
    )

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_collection_result)

    async def mock_db():
        yield db

    class FakeLocalRAGService:
        def __init__(self, service_db, user_id: str):
            calls["db"] = service_db
            calls["user_id"] = user_id

        async def get_collection_evidence(
            self,
            service_collection_id: str,
            question: str,
            top_k: int = 15,
        ) -> dict[str, object]:
            calls["evidence"] = (service_collection_id, question, top_k)
            return {
                "enabled": True,
                "backend": "local",
                "chunks": [{"id": "chunk-1", "source": "local"}],
                "total": 1,
            }

    app.dependency_overrides[get_db] = mock_db
    monkeypatch.setattr("app.api.v1.ragflow.LocalRAGService", FakeLocalRAGService)

    original_enabled = settings.ragflow_sync_enabled
    settings.ragflow_sync_enabled = False
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/v1/workspaces/{collection_id}/evidence",
                params={"q": "Which methods changed?", "top_k": 7},
            )
    finally:
        settings.ragflow_sync_enabled = original_enabled
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "enabled": True,
        "backend": "local",
        "chunks": [{"id": "chunk-1", "source": "local"}],
        "total": 1,
    }
    assert calls == {
        "db": db,
        "user_id": DEFAULT_USER_ID,
        "evidence": (str(collection_id), "Which methods changed?", 7),
    }
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_workspace_ask_degraded_on_httpx_error(monkeypatch: pytest.MonkeyPatch):
    """Workspace ask should degrade gracefully when the RAGFlow sidecar is unavailable."""
    from app.config import settings
    from app.dependencies import get_db
    from app.main import app

    collection_id = uuid4()
    mock_collection_result = MagicMock()
    mock_collection_result.scalar_one_or_none.return_value = SimpleNamespace(
        id=collection_id,
        name="Workspace",
        deleted_at=None,
    )

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_collection_result)

    async def mock_db():
        yield db

    async def mock_get_by_collection_id(*_args, **_kwargs):
        return SimpleNamespace(
            ragflow_dataset_id="ds_workspace",
            parse_status="done",
        )

    async def mock_chat_completion(*_args, **_kwargs):
        raise httpx.HTTPError("ragflow down")

    app.dependency_overrides[get_db] = mock_db
    monkeypatch.setattr(
        "app.services.ragflow.dataset_registry.DatasetRegistryService.get_by_collection_id",
        mock_get_by_collection_id,
    )
    monkeypatch.setattr(
        "app.services.ragflow.ragflow_client.RagflowClient.chat_completion",
        mock_chat_completion,
    )

    original_enabled = settings.ragflow_sync_enabled
    settings.ragflow_sync_enabled = True
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/workspaces/{collection_id}/ask",
                json={"question": "What changed?", "top_k": 10},
            )
    finally:
        settings.ragflow_sync_enabled = original_enabled
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["answer"] is None
    assert payload["sources"] == []
    assert payload["error"] == "ragflow_unavailable"


@pytest.mark.asyncio
async def test_sync_paper_no_content_cleans_stale_mapping(
    monkeypatch: pytest.MonkeyPatch,
):
    """Paper sync should remove stale RAGFlow state when no markdown remains."""
    from app.services.ragflow.document_sync_service import DocumentSyncService

    paper_id = str(uuid4())
    mapping = SimpleNamespace(
        id=uuid4(),
        ragflow_dataset_id="ds_paper",
        ragflow_document_id="doc_paper",
    )

    ragflow_client = MagicMock()
    ragflow_client.delete_document = AsyncMock(return_value=True)

    registry = MagicMock()
    registry.get_by_paper_id = AsyncMock(return_value=mapping)
    registry.delete_by_paper_id = AsyncMock()

    service = DocumentSyncService(
        db=MagicMock(),
        ragflow_client=ragflow_client,
        registry=registry,
    )
    service._get_paper = AsyncMock(return_value=SimpleNamespace(id=paper_id))

    monkeypatch.setattr(
        "app.services.ragflow.document_sync_service.settings.ragflow_sync_enabled",
        True,
    )
    monkeypatch.setattr(
        "app.services.ragflow.document_sync_service.TextChunker.prepare_paper_text",
        lambda _paper: "",
    )

    result = await service.sync_paper(paper_id)

    assert result["enabled"] is True
    assert result["status"] == "no_content"
    ragflow_client.delete_document.assert_awaited_once_with("ds_paper", "doc_paper")
    registry.delete_by_paper_id.assert_awaited_once_with(paper_id)


def test_reconcile_disabled_returns_early(monkeypatch: pytest.MonkeyPatch):
    """Reconcile should short-circuit cleanly when the RAGFlow feature flag is off."""
    from app.services.ragflow.ragflow_sync_tasks import reconcile_sync_task

    monkeypatch.setattr(
        "app.services.ragflow.ragflow_sync_tasks.settings.ragflow_sync_enabled",
        False,
    )

    result = reconcile_sync_task()

    assert result == {"skipped": True}


@pytest.mark.asyncio
async def test_workspace_ask_disabled_requires_collection_before_local_fallback(
    monkeypatch: pytest.MonkeyPatch,
):
    """Workspace ask should validate collection access before local fallback."""
    from app.config import settings
    from app.dependencies import get_db
    from app.main import app

    collection_id = uuid4()
    mock_collection_result = MagicMock()
    mock_collection_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_collection_result)

    async def mock_db():
        yield db

    class FailingLocalRAGService:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("local fallback should not start")

    app.dependency_overrides[get_db] = mock_db
    monkeypatch.setattr("app.api.v1.ragflow.LocalRAGService", FailingLocalRAGService)

    original_enabled = settings.ragflow_sync_enabled
    settings.ragflow_sync_enabled = False
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/workspaces/{collection_id}/ask",
                json={"question": "What changed?", "top_k": 10},
            )
    finally:
        settings.ragflow_sync_enabled = original_enabled
        app.dependency_overrides.clear()

    assert response.status_code == 404
    payload = response.json()
    assert payload["message"] == "Collection not found"
    assert payload["code"] == "HTTP_404"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_status_endpoint():
    """Sync status endpoint should return a 200 response with basic status data."""
    from app.dependencies import get_db
    from app.main import app

    paper_count_result = MagicMock()
    paper_count_result.scalar.return_value = 0

    db = MagicMock()
    db.execute = AsyncMock(return_value=paper_count_result)

    async def mock_db():
        yield db

    app.dependency_overrides[get_db] = mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/ragflow/sync/status")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert "enabled" in payload
    assert "freshness_minutes" in payload

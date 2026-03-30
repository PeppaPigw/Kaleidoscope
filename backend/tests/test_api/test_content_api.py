"""API integration tests for content endpoints."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient


def test_health_check_includes_service_metadata():
    """Health check returns versioned service metadata."""
    from app.main import app

    async def run_test():
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            return await client.get("/health")

    response = asyncio.run(run_test())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["timestamp"].endswith("Z")
    assert data["services"] == {"database": "unknown"}


def test_get_import_status_returns_current_paper_state():
    """Import status returns the paper's current ingestion fields."""
    from app.dependencies import get_db
    from app.main import app

    paper_id = uuid4()
    paper = MagicMock()
    paper.id = paper_id
    paper.title = "Imported paper"
    paper.ingestion_status = "parsed"
    paper.has_full_text = True
    paper.created_at = datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc)
    paper.updated_at = datetime(2026, 3, 30, 12, 5, tzinfo=timezone.utc)
    paper.raw_metadata = {"import_error": "MinerU timeout"}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = paper

    async def mock_db():
        db = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)
        yield db

    app.dependency_overrides[get_db] = mock_db
    try:
        async def run_test():
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                return await client.get(f"/api/v1/papers/{paper_id}/import-status")

        response = asyncio.run(run_test())
        assert response.status_code == 200
        data = response.json()
        assert data["paper_id"] == str(paper_id)
        assert data["title"] == "Imported paper"
        assert data["ingestion_status"] == "parsed"
        assert data["has_full_text"] is True
        assert data["error_message"] == "MinerU timeout"
    finally:
        app.dependency_overrides.clear()

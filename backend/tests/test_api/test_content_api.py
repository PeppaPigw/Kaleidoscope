"""API integration tests for content endpoints."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient


def test_health_check_includes_service_metadata():
    """Health check returns versioned service metadata."""
    from app.main import app

    async def run_test():
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-API-Key": "sk-kaleidoscope"},
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
    paper.created_at = datetime(2026, 3, 30, 12, 0, tzinfo=UTC)
    paper.updated_at = datetime(2026, 3, 30, 12, 5, tzinfo=UTC)
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
                headers={"X-API-Key": "sk-kaleidoscope"},
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


def test_get_paper_content_tolerates_legacy_figures_dict():
    """Content endpoint should not 500 when historical rows store a dict in parsed_figures."""
    from app.dependencies import get_db
    from app.main import app

    paper_id = uuid4()
    paper = MagicMock()
    paper.id = paper_id
    paper.title = "Legacy MinerU Paper"
    paper.abstract = "Short abstract."
    paper.deleted_at = None
    paper.full_text_markdown = "# Legacy MinerU Paper\n\nThis paper has full text."
    paper.remote_urls = [{"url": "https://example.com/paper.pdf", "type": "pdf"}]
    paper.markdown_provenance = {"source": "mineru"}
    paper.parsed_sections = [
        {"title": "Intro", "level": 1, "paragraphs": ["First paragraph."]},
    ]
    paper.parsed_figures = {
        "_backend": "hybrid",
        "enable_vlm": True,
    }

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
                headers={"X-API-Key": "sk-kaleidoscope"},
            ) as client:
                return await client.get(f"/api/v1/papers/{paper_id}/content")

        response = asyncio.run(run_test())
        assert response.status_code == 200
        data = response.json()
        assert data["paper_id"] == str(paper_id)
        assert data["format"] == "markdown"
        assert data["figures"] == []
        assert data["sections"] == [
            {"title": "Intro", "level": 1, "paragraphs": ["First paragraph."]},
        ]
    finally:
        app.dependency_overrides.clear()


def test_get_paper_labels_rejects_stale_empty_payloads():
    from app.dependencies import get_db
    from app.main import app

    paper_id = uuid4()
    paper = MagicMock()
    paper.id = paper_id
    paper.deleted_at = None
    paper.has_full_text = True
    paper.abstract = "Abstract"
    paper.paper_labels = {
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
    paper.paper_labels_at = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)

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
                headers={"X-API-Key": "sk-kaleidoscope"},
            ) as client:
                return await client.get(f"/api/v1/papers/{paper_id}/labels")

        response = asyncio.run(run_test())
        assert response.status_code == 404
        payload = response.json()
        message = payload.get("detail") or payload.get("message") or ""
        assert message.startswith("Labels not generated yet")
    finally:
        app.dependency_overrides.clear()


def test_get_deep_analysis_rejects_empty_prompt_artifacts():
    from app.dependencies import get_db
    from app.main import app

    paper_id = uuid4()
    paper = MagicMock()
    paper.id = paper_id
    paper.deleted_at = None
    paper.deep_analysis = {
        "status": "ok",
        "analysis": "[EXT] *Note: As the prompt provided empty fields for the paper's Abstract and Full Text...",
        "fulltext_chars": 0,
    }

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
                headers={"X-API-Key": "sk-kaleidoscope"},
            ) as client:
                return await client.get(f"/api/v1/papers/{paper_id}/deep-analysis")

        response = asyncio.run(run_test())
        assert response.status_code == 404
        payload = response.json()
        message = payload.get("detail") or payload.get("message") or ""
        assert message == "Deep analysis not available"
    finally:
        app.dependency_overrides.clear()

"""API integration tests for papers endpoints."""

import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient


def test_health_check():
    """Test the health check endpoint."""
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


def test_list_papers_empty():
    """Test list papers returns empty result when db returns nothing."""
    from app.dependencies import get_db
    from app.main import app

    async def mock_db():
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
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
                return await client.get("/api/v1/papers")

        response = asyncio.run(run_test())
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] == 0
        assert data["items"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_paper_not_found():
    """Test getting a non-existent paper returns 404."""
    from app.dependencies import get_db
    from app.main import app

    async def mock_db():
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        yield db

    app.dependency_overrides[get_db] = mock_db
    try:
        paper_id = str(uuid4())

        async def run_test():
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers={"X-API-Key": "sk-kaleidoscope"},
            ) as client:
                return await client.get(f"/api/v1/papers/{paper_id}")

        response = asyncio.run(run_test())
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_paper_includes_venue_and_raw_metadata():
    """Test getting a paper includes venue name and raw metadata payload."""
    from app.dependencies import get_db
    from app.main import app

    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        doi="10.1000/test",
        arxiv_id="2501.00001",
        pmid=None,
        title="Venue-aware paper",
        abstract="A paper abstract.",
        published_at=date(2025, 1, 15),
        paper_type="article",
        oa_status="gold",
        language="en",
        keywords=["agents", "retrieval"],
        citation_count=7,
        has_full_text=True,
        ingestion_status="indexed",
        summary="Summary",
        highlights=["Highlight"],
        contributions=["Contribution"],
        limitations=["Limitation"],
        authors=[],
        venue=SimpleNamespace(name="ICML 2025"),
        raw_metadata={"pdf_url": "https://example.com/paper.pdf"},
        created_at=datetime(2025, 1, 15, tzinfo=UTC),
        updated_at=datetime(2025, 1, 16, tzinfo=UTC),
    )

    async def mock_db():
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = paper
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
                return await client.get(f"/api/v1/papers/{paper_id}")

        response = asyncio.run(run_test())
        assert response.status_code == 200
        data = response.json()
        assert data["venue"] == "ICML 2025"
        assert data["raw_metadata"] == {"pdf_url": "https://example.com/paper.pdf"}
    finally:
        app.dependency_overrides.clear()


def test_intelligence_summarize_not_found():
    """Test that summarize returns 404 for missing paper."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    from httpx import ASGITransport, AsyncClient

    async def run():
        from app.dependencies import get_db
        from app.main import app

        async def mock_db():
            db = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db.execute = AsyncMock(return_value=mock_result)
            yield db

        app.dependency_overrides[get_db] = mock_db
        try:
            paper_id = str(uuid4())
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers={"X-API-Key": "sk-kaleidoscope"},
            ) as client:
                response = await client.post(
                    f"/api/v1/intelligence/papers/{paper_id}/summarize"
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    asyncio.run(run())

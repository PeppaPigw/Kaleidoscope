"""Regression tests for search, intelligence, and reasoning API contracts."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient


def _mock_db_with_scalars(items):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items
    mock_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_result)
    return db


@pytest.mark.asyncio
async def test_search_browse_returns_discovery_feed():
    from app.dependencies import get_db
    from app.main import app

    papers = [
        SimpleNamespace(
            id=uuid4(),
            title="Newest Paper",
            abstract="Recent abstract",
            doi="10.1000/new",
            arxiv_id="2501.00001",
            published_at=None,
            citation_count=12,
            created_at="2026-03-31T00:00:00Z",
            deleted_at=None,
        ),
        SimpleNamespace(
            id=uuid4(),
            title="Older Paper",
            abstract="Older abstract",
            doi=None,
            arxiv_id=None,
            published_at=None,
            citation_count=3,
            created_at="2026-03-30T00:00:00Z",
            deleted_at=None,
        ),
    ]

    async def mock_db():
        yield _mock_db_with_scalars(papers)

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/search/browse?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "browse"
        assert data["total"] == 2
        assert data["hits"][0]["title"] == "Newest Paper"
        assert data["hits"][0]["paper_id"]
        assert data["hits"][0]["score"] == 1.0
        assert data["hits"][0]["authors"] == []
        assert data["hits"][0]["venue"] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_similar_papers_response_is_wrapped_and_renamed(monkeypatch):
    from app.api.v1 import intelligence as intelligence_api
    from app.dependencies import get_db
    from app.main import app

    async def mock_get_paper(self, paper_id):
        return {"id": paper_id}

    async def mock_get_similar(self, paper_id, top_k):
        assert top_k == 3
        return [
            {
                "id": "paper-2",
                "title": "Neighbor Paper",
                "similarity_score": 0.91,
                "doi": "10.1000/neighbor",
                "published_at": "2025-01-01",
                "citation_count": 7,
                "reason": "Shared methods",
            }
        ]

    monkeypatch.setattr(
        intelligence_api.IntelligenceService,
        "_get_paper",
        mock_get_paper,
    )
    monkeypatch.setattr(
        intelligence_api.IntelligenceService,
        "get_similar_papers",
        mock_get_similar,
    )

    async def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/api/v1/intelligence/papers/{uuid4()}/similar?top_k=3"
            )

        assert response.status_code == 200
        data = response.json()
        assert list(data.keys()) == ["similar_papers"]
        assert data["similar_papers"] == [
            {
                "paper_id": "paper-2",
                "title": "Neighbor Paper",
                "score": 0.91,
                "doi": "10.1000/neighbor",
                "published_at": "2025-01-01",
                "citation_count": 7,
                "reason": "Shared methods",
            }
        ]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analysis_missing_paper_becomes_404(monkeypatch):
    from app.api.v1 import analysis as analysis_api
    from app.dependencies import get_db
    from app.main import app

    async def mock_analyze(self, paper_id):
        raise ValueError(f"Paper not found: {paper_id}")

    async def mock_close(self):
        return None

    monkeypatch.setattr(
        analysis_api.DeepAnalysisService, "analyze_innovation", mock_analyze
    )
    monkeypatch.setattr(analysis_api.DeepAnalysisService, "close", mock_close)

    async def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/analysis/papers/{uuid4()}/innovation"
            )

        assert response.status_code == 404
        assert "Paper not found" in response.json()["message"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_writing_service_failures_become_502(monkeypatch):
    from app.api.v1 import writing as writing_api
    from app.dependencies import get_db
    from app.main import app

    async def mock_generate(self, paper_ids, style, format_):
        raise RuntimeError("model backend timeout")

    async def mock_close(self):
        return None

    monkeypatch.setattr(
        writing_api.WritingService, "generate_related_work", mock_generate
    )
    monkeypatch.setattr(writing_api.WritingService, "close", mock_close)

    async def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/writing/related-work",
                json={
                    "paper_ids": ["paper-1"],
                    "style": "narrative",
                    "format": "markdown",
                },
            )

        assert response.status_code == 502
        assert response.json()["message"].startswith("Writing service error:")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cross_paper_embedded_errors_become_http_404(monkeypatch):
    from app.dependencies import get_db
    from app.main import app
    from app.services.analysis import cross_paper_service

    async def mock_synthesize(self, paper_ids, topic):
        return {"error": "No papers found"}

    async def mock_close(self):
        return None

    monkeypatch.setattr(
        cross_paper_service.CrossPaperService, "synthesize", mock_synthesize
    )
    monkeypatch.setattr(cross_paper_service.CrossPaperService, "close", mock_close)

    async def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/cross-paper/synthesize",
                json={"paper_ids": ["paper-1"], "topic": "agents"},
            )

        assert response.status_code == 404
        assert response.json()["message"] == "No papers found"
    finally:
        app.dependency_overrides.clear()

"""Unit tests for the Data Analytics module.

Tests:
- app/schemas/trends.py        — schema instantiation
- app/schemas/researchers.py   — schema instantiation
- app/services/analysis/trend_service.py — keyword_timeseries, keyword_cooccurrence
- app/services/analysis/researcher_service.py — emerging_authors, collaboration_network
"""

from __future__ import annotations

import pytest
from collections import Counter
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Schema smoke tests ───────────────────────────────────────────


def test_keyword_trend_item_schema():
    from app.schemas.trends import KeywordTrendItem
    item = KeywordTrendItem(
        keyword="transformer",
        total_count=100,
        growth_rate=1.5,
        trend="rising",
        per_year={"2022": 30, "2023": 70},
    )
    assert item.keyword == "transformer"
    assert item.trend == "rising"


def test_keyword_timeseries_response_schema():
    from app.schemas.trends import KeywordTimeseriesResponse, KeywordTimeseriesItem, KeywordTimePoint
    resp = KeywordTimeseriesResponse(
        keywords=[
            KeywordTimeseriesItem(
                keyword="BERT",
                series=[KeywordTimePoint(year=2022, count=10)],
                total=10,
            )
        ],
        years_covered=[2022],
    )
    assert resp.keywords[0].keyword == "BERT"
    assert resp.years_covered == [2022]


def test_cooccurrence_response_schema():
    from app.schemas.trends import KeywordCooccurrenceResponse, CooccurrenceEdge
    resp = KeywordCooccurrenceResponse(
        edges=[CooccurrenceEdge(keyword_a="NLP", keyword_b="BERT", count=5)],
        total_papers_analyzed=20,
    )
    assert resp.edges[0].count == 5


def test_sleeping_papers_response_schema():
    from app.schemas.trends import SleepingPapersResponse, SleepingPaperItem
    resp = SleepingPapersResponse(
        papers=[
            SleepingPaperItem(
                id="abc",
                title="Old but Gold",
                citation_count=200,
                years_old=8,
                proxy_score=70.7,
            )
        ]
    )
    assert resp.papers[0].proxy_score == 70.7


def test_emerging_author_schema():
    from app.schemas.researchers import EmergingAuthorItem, EmergingAuthorsResponse
    resp = EmergingAuthorsResponse(
        authors=[
            EmergingAuthorItem(
                id="a1",
                display_name="Alice",
                paper_count=5,
                total_citations=120,
            )
        ]
    )
    assert resp.authors[0].total_citations == 120


def test_author_profile_schema():
    from app.schemas.researchers import AuthorProfileResponse, YearlyPub, PaperSummary
    resp = AuthorProfileResponse(
        id="a1",
        display_name="Bob",
        paper_count_in_library=3,
        total_citations_in_library=50,
        timeline=[YearlyPub(year=2023, count=2), YearlyPub(year=2024, count=1)],
        top_papers=[
            PaperSummary(
                id="p1",
                title="Great Paper",
                citation_count=30,
                author_position=0,
                is_corresponding=True,
            )
        ],
    )
    assert resp.timeline[0].year == 2023


def test_collaboration_network_schema():
    from app.schemas.researchers import (
        CollaborationNetworkResponse,
        NetworkNode,
        NetworkEdge,
    )
    resp = CollaborationNetworkResponse(
        nodes=[NetworkNode(id="a1", label="Alice", paper_count=5)],
        edges=[NetworkEdge(source="a1", target="a2", weight=3)],
    )
    assert resp.edges[0].weight == 3


# ─── TrendService unit tests ──────────────────────────────────────


class FakeResult:
    """Mimics SQLAlchemy async result."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalar(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None


def _make_paper(kw_list, year):
    """Create a mock Paper-like object."""
    p = MagicMock()
    p.keywords = kw_list
    pub = MagicMock()
    pub.year = year
    p.published_at = pub
    return p


def _make_row(kw_list):
    row = MagicMock()
    row.keywords = kw_list
    pub = MagicMock()
    pub.year = 2023
    row.published_at = pub
    return row


@pytest.mark.asyncio
async def test_keyword_timeseries_basic():
    """keyword_timeseries returns correct per-year counts."""
    from app.services.analysis.trend_service import TrendService

    # Two rows: both in 2022, one has "transformer" and "attention"
    row1 = MagicMock()
    row1.keywords = ["transformer", "attention"]
    p1 = MagicMock(); p1.year = 2022
    row1.published_at = p1

    row2 = MagicMock()
    row2.keywords = ["transformer"]
    p2 = MagicMock(); p2.year = 2022
    row2.published_at = p2

    mock_db = AsyncMock()
    fake = FakeResult([row1, row2])
    mock_db.execute.return_value = fake

    svc = TrendService(mock_db)
    result = await svc.keyword_timeseries(keywords=["transformer", "attention"], years_back=3)

    # Check structure
    assert "keywords" in result
    assert "years_covered" in result

    kw_map = {item["keyword"]: item for item in result["keywords"]}
    assert kw_map["transformer"]["total"] == 2
    assert kw_map["attention"]["total"] == 1


@pytest.mark.asyncio
async def test_keyword_timeseries_empty():
    """keyword_timeseries with no matching papers returns empty series."""
    from app.services.analysis.trend_service import TrendService

    mock_db = AsyncMock()
    mock_db.execute.return_value = FakeResult([])

    svc = TrendService(mock_db)
    result = await svc.keyword_timeseries(keywords=["xyz"], years_back=3)

    assert result["years_covered"] == []
    assert result["keywords"][0]["total"] == 0


@pytest.mark.asyncio
async def test_keyword_cooccurrence_basic():
    """keyword_cooccurrence builds correct edge list."""
    from app.services.analysis.trend_service import TrendService

    # One paper with three keywords
    row = MagicMock()
    row.keywords = ["deep learning", "neural network", "attention"]

    mock_db = AsyncMock()
    # First call: get keywords for frequency, second call: same data
    mock_db.execute.return_value = FakeResult([(["deep learning", "neural network", "attention"],)])

    svc = TrendService(mock_db)
    result = await svc.keyword_cooccurrence(
        top_keywords=10,
        years_back=3,
        min_cooccurrence=1,
    )

    assert "edges" in result
    assert result["total_papers_analyzed"] == 1
    # Should have 3 edges (C(3,2)=3 pairs)
    assert len(result["edges"]) == 3


@pytest.mark.asyncio
async def test_keyword_cooccurrence_min_filter():
    """min_cooccurrence filters out rare pairs."""
    from app.services.analysis.trend_service import TrendService

    # Two papers; only one pair co-occurs twice
    rows = [
        (["A", "B"],),
        (["A", "B"],),
        (["A", "C"],),   # A-C only appears once
    ]

    mock_db = AsyncMock()
    mock_db.execute.return_value = FakeResult(rows)

    svc = TrendService(mock_db)
    result = await svc.keyword_cooccurrence(
        top_keywords=10,
        years_back=3,
        min_cooccurrence=2,
    )

    # Only A-B should pass (count=2); A-C filtered out
    edges = result["edges"]
    edge_pairs = [(e["keyword_a"], e["keyword_b"]) for e in edges]
    assert ("a", "b") in edge_pairs
    assert ("a", "c") not in edge_pairs


# ─── ResearcherService unit tests ────────────────────────────────


@pytest.mark.asyncio
async def test_get_author_profile_not_found():
    """get_author_profile returns None for unknown author."""
    from app.services.analysis.researcher_service import ResearcherService

    mock_db = AsyncMock()

    # Simulate scalar_one_or_none returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    svc = ResearcherService(mock_db)
    result = await svc.get_author_profile("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_collaboration_network_empty_graph():
    """collaboration_network returns empty nodes/edges when no data."""
    from app.services.analysis.researcher_service import ResearcherService

    mock_db = AsyncMock()
    mock_db.execute.return_value = FakeResult([])

    svc = ResearcherService(mock_db)
    result = await svc.collaboration_network(author_id=None, top_k=10, min_collaborations=2)

    assert result["nodes"] == []
    assert result["edges"] == []
    assert result["center_author_id"] is None

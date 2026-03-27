"""Unit tests for analysis extension services."""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


if "structlog" not in sys.modules:
    _logger = SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        bind=lambda *args, **kwargs: None,
    )
    sys.modules["structlog"] = SimpleNamespace(
        get_logger=lambda *args, **kwargs: _logger
    )


class FakeResult:
    """Simple SQLAlchemy result stub for service tests."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self


def make_db(*execute_results):
    return SimpleNamespace(execute=AsyncMock(side_effect=list(execute_results)))


def test_trend_extensions_topic_evolution_and_expert_finder():
    """Keyword trend aggregation and expert ranking handle normalized keywords."""
    from app.services.analysis.trend_extensions import TrendExtensionsService

    evolution_db = make_db(
        FakeResult(
            [
                SimpleNamespace(
                    keywords=["AI", "ML", "AI"],
                    published_at=date(2020, 5, 1),
                ),
                SimpleNamespace(
                    keywords={"keywords": ["AI", "Robotics"]},
                    published_at=date(2021, 5, 1),
                ),
                SimpleNamespace(
                    keywords=["ML", "Vision"],
                    published_at=date(2021, 6, 1),
                ),
            ]
        )
    )
    expert_db = make_db(
        FakeResult(
            [
                SimpleNamespace(
                    author_id=uuid4(),
                    display_name="Ada Lovelace",
                    institution_id=uuid4(),
                    paper_id=uuid4(),
                    keywords=["AI", "ML"],
                    citation_count=25,
                ),
                SimpleNamespace(
                    author_id=uuid4(),
                    display_name="Grace Hopper",
                    institution_id=None,
                    paper_id=uuid4(),
                    keywords=["AI", "ML"],
                    citation_count=10,
                ),
                SimpleNamespace(
                    author_id=uuid4(),
                    display_name="Linus Torvalds",
                    institution_id=None,
                    paper_id=uuid4(),
                    keywords=["AI", "Systems"],
                    citation_count=100,
                ),
            ]
        )
    )

    evolution_service = TrendExtensionsService(evolution_db)
    expert_service = TrendExtensionsService(expert_db)

    async def run_test():
        evolution = await evolution_service.get_topic_evolution(
            top_keywords=3,
            start_year=2020,
        )
        assert evolution == {
            "keywords": ["ai", "ml", "robotics"],
            "years": [2020, 2021],
            "matrix": {
                "ai": {2020: 1, 2021: 1},
                "ml": {2020: 1, 2021: 1},
                "robotics": {2020: 0, 2021: 1},
            },
        }

        experts = await expert_service.get_expert_finder(["ai", "ml"], top_k=5)
        assert [expert["display_name"] for expert in experts] == [
            "Ada Lovelace",
            "Grace Hopper",
        ]
        assert experts[0]["matching_papers"] == 1
        assert experts[0]["total_citations"] == 25

    asyncio.run(run_test())


def test_trend_extensions_venue_ranking_and_direction_change():
    """Venue aggregates and researcher topic shifts are serialized correctly."""
    from app.services.analysis.trend_extensions import TrendExtensionsService

    venue_id = uuid4()
    ranking_db = make_db(
        FakeResult(
            [
                SimpleNamespace(
                    venue_id=venue_id,
                    name="Journal of Useful Models",
                    paper_count=3,
                    total_citations=45,
                    avg_citations=15.0,
                )
            ]
        )
    )
    direction_db = make_db(
        FakeResult(
            [
                SimpleNamespace(
                    published_at=date(2018, 1, 1),
                    keywords=["Vision", "CNN"],
                ),
                SimpleNamespace(
                    published_at=date(2019, 1, 1),
                    keywords=["Vision"],
                ),
                SimpleNamespace(
                    published_at=date(2022, 1, 1),
                    keywords=["Transformer", "NLP"],
                ),
                SimpleNamespace(
                    published_at=date(2023, 1, 1),
                    keywords=["Transformer", "Multimodal"],
                ),
            ]
        )
    )

    ranking_service = TrendExtensionsService(ranking_db)
    direction_service = TrendExtensionsService(direction_db)

    async def run_test():
        ranking = await ranking_service.get_venue_ranking(limit=10)
        assert ranking == [
            {
                "venue_id": str(venue_id),
                "name": "Journal of Useful Models",
                "paper_count": 3,
                "total_citations": 45,
                "avg_citations": 15.0,
            }
        ]

        direction = await direction_service.get_researcher_direction_change(
            author_id="author-1",
            window_years=2,
        )
        assert direction["old_keywords"] == ["vision", "cnn"]
        assert direction["new_keywords"] == ["transformer", "multimodal", "nlp"]
        assert direction["stable"] == []
        assert direction["dropped"] == ["cnn", "vision"]
        assert direction["gained"] == ["multimodal", "nlp", "transformer"]

    asyncio.run(run_test())


def test_knowledge_ext_quiz_and_glossary():
    """Quiz generation is deterministic and glossary merges stored plus auto terms."""
    from app.services.analysis.knowledge_service_ext import KnowledgeExtService

    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Graph Neural Networks for Drug Discovery",
        abstract=(
            "This paper studies graph neural networks for molecular property prediction. "
            "It contributes to drug discovery workflows. "
            "Results show improved accuracy on benchmark tasks."
        ),
        published_at=date(2024, 5, 1),
        keywords=["Graph Neural Networks", "Drug Discovery"],
    )
    glossary_term = SimpleNamespace(
        term="Graph Neural Networks",
        definition="Neural architectures that operate on graph-structured data.",
        is_auto_generated=False,
    )

    db = make_db(
        FakeResult([paper]),
        FakeResult([paper]),
        FakeResult([glossary_term]),
    )
    service = KnowledgeExtService(db)

    async def run_test():
        quiz = await service.generate_quiz(str(paper_id))
        assert quiz["paper_id"] == str(paper_id)
        assert len(quiz["questions"]) == 3
        assert "2024" in quiz["questions"][2]["options"]
        assert quiz["questions"][2]["options"][quiz["questions"][2]["correct_index"]] == "2024"

        glossary = await service.get_glossary(str(paper_id))
        assert glossary == {
            "paper_id": str(paper_id),
            "terms": [
                {
                    "term": "Drug Discovery",
                    "definition": None,
                    "source": "auto",
                    "in_abstract": True,
                },
                {
                    "term": "Graph Neural Networks",
                    "definition": "Neural architectures that operate on graph-structured data.",
                    "source": "user",
                    "in_abstract": True,
                },
            ],
        }

    asyncio.run(run_test())


def test_knowledge_ext_retraction_stats():
    """Retraction stats aggregate year buckets and source buckets."""
    from app.services.analysis.knowledge_service_ext import KnowledgeExtService

    db = make_db(
        FakeResult(
            [
                SimpleNamespace(
                    published_at=date(2021, 1, 1),
                    ingestion_status="retracted",
                    raw_metadata=None,
                    source_type="remote",
                ),
                SimpleNamespace(
                    published_at=date(2022, 1, 1),
                    ingestion_status="indexed",
                    raw_metadata={"retraction": {"source": "openalex"}},
                    source_type="remote",
                ),
                SimpleNamespace(
                    published_at=date(2022, 6, 1),
                    ingestion_status="retracted",
                    raw_metadata={"retraction": {"provider": "crossref"}},
                    source_type="local_upload",
                ),
            ]
        )
    )
    service = KnowledgeExtService(db)

    async def run_test():
        stats = await service.get_retraction_stats(min_year=2020)
        assert stats == {
            "total_retracted": 3,
            "by_year": [
                {"year": 2021, "count": 1},
                {"year": 2022, "count": 2},
            ],
            "by_source": [
                {"source": "crossref", "count": 1},
                {"source": "ingestion_status", "count": 1},
                {"source": "openalex", "count": 1},
            ],
        }

    asyncio.run(run_test())

"""Extended trend and expert analytics for Kaleidoscope."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import Author, PaperAuthor
from app.models.paper import Paper
from app.models.venue import Venue

logger = structlog.get_logger(__name__)


class TrendExtensionsService:
    """Additional trend-analysis helpers built on the local paper graph."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_topic_evolution(
        self, top_keywords: int = 10, start_year: int = 2010
    ) -> dict:
        """Return annual keyword counts for the most common keywords."""
        cutoff = date(start_year, 1, 1)
        result = await self.db.execute(
            select(Paper.keywords, Paper.published_at)
            .where(
                Paper.deleted_at.is_(None),
                Paper.published_at.is_not(None),
                Paper.published_at >= cutoff,
                Paper.keywords.is_not(None),
            )
            .order_by(Paper.published_at.asc())
        )

        yearly_counts: dict[int, Counter[str]] = defaultdict(Counter)
        total_counts: Counter[str] = Counter()

        for row in result.all():
            if not row.published_at:
                continue
            year = row.published_at.year
            keywords = self._keyword_list(row.keywords)
            yearly_counts[year].update(keywords)
            total_counts.update(keywords)

        years = sorted(yearly_counts.keys())
        keyword_limit = max(top_keywords, 0)
        selected_keywords = [
            keyword for keyword, _ in total_counts.most_common(keyword_limit)
        ]
        matrix = {
            keyword: {year: yearly_counts[year].get(keyword, 0) for year in years}
            for keyword in selected_keywords
        }

        logger.info(
            "topic_evolution_computed",
            years=len(years),
            tracked_keywords=len(selected_keywords),
        )
        return {
            "keywords": selected_keywords,
            "years": years,
            "matrix": matrix,
        }

    async def get_expert_finder(
        self, keywords: list[str], top_k: int = 10
    ) -> list[dict]:
        """Find authors with papers matching all requested keywords."""
        target_keywords = {kw.casefold() for kw in self._keyword_list(keywords)}
        if not target_keywords or top_k <= 0:
            return []

        result = await self.db.execute(
            select(
                Author.id.label("author_id"),
                Author.display_name,
                Author.institution_id,
                Paper.id.label("paper_id"),
                Paper.keywords,
                Paper.citation_count,
            )
            .join(PaperAuthor, PaperAuthor.author_id == Author.id)
            .join(Paper, Paper.id == PaperAuthor.paper_id)
            .where(
                Author.deleted_at.is_(None),
                Paper.deleted_at.is_(None),
                Paper.keywords.is_not(None),
            )
        )

        author_stats: dict[str, dict] = {}
        seen_author_papers: set[tuple[str, str]] = set()

        for row in result.all():
            paper_keywords = {kw.casefold() for kw in self._keyword_list(row.keywords)}
            if not target_keywords.issubset(paper_keywords):
                continue

            author_id = str(row.author_id)
            paper_id = str(row.paper_id)
            pair = (author_id, paper_id)
            if pair in seen_author_papers:
                continue
            seen_author_papers.add(pair)

            if author_id not in author_stats:
                author_stats[author_id] = {
                    "author_id": author_id,
                    "display_name": row.display_name,
                    "matching_papers": 0,
                    "total_citations": 0,
                    "institution_id": (
                        str(row.institution_id) if row.institution_id else None
                    ),
                }

            author_stats[author_id]["matching_papers"] += 1
            author_stats[author_id]["total_citations"] += row.citation_count or 0

        ranked_authors = sorted(
            author_stats.values(),
            key=lambda item: (
                -item["matching_papers"],
                -item["total_citations"],
                item["display_name"].casefold(),
            ),
        )
        return ranked_authors[:top_k]

    async def get_venue_ranking(self, limit: int = 50) -> list[dict]:
        """Rank venues by average citations per paper."""
        avg_citations = func.coalesce(func.avg(func.coalesce(Paper.citation_count, 0)), 0.0)
        total_citations = func.coalesce(func.sum(Paper.citation_count), 0)
        paper_count = func.count(Paper.id)

        result = await self.db.execute(
            select(
                Venue.id.label("venue_id"),
                Venue.name,
                paper_count.label("paper_count"),
                total_citations.label("total_citations"),
                avg_citations.label("avg_citations"),
            )
            .join(Paper, Paper.venue_id == Venue.id)
            .where(
                Venue.deleted_at.is_(None),
                Paper.deleted_at.is_(None),
            )
            .group_by(Venue.id, Venue.name)
            .order_by(avg_citations.desc(), total_citations.desc(), Venue.name.asc())
            .limit(limit)
        )

        return [
            {
                "venue_id": str(row.venue_id),
                "name": row.name,
                "paper_count": row.paper_count or 0,
                "total_citations": row.total_citations or 0,
                "avg_citations": float(row.avg_citations or 0.0),
            }
            for row in result.all()
        ]

    async def get_researcher_direction_change(
        self, author_id: str, window_years: int = 3
    ) -> dict:
        """Compare older and newer keyword windows for a given researcher."""
        result = await self.db.execute(
            select(Paper.published_at, Paper.keywords)
            .join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
            .where(
                PaperAuthor.author_id == author_id,
                Paper.deleted_at.is_(None),
                Paper.published_at.is_not(None),
                Paper.keywords.is_not(None),
            )
            .order_by(Paper.published_at.asc(), Paper.created_at.asc())
        )

        yearly_counts: dict[int, Counter[str]] = defaultdict(Counter)
        for row in result.all():
            if not row.published_at:
                continue
            yearly_counts[row.published_at.year].update(self._keyword_list(row.keywords))

        years = sorted(yearly_counts.keys())
        if not years:
            return {
                "author_id": author_id,
                "old_keywords": [],
                "new_keywords": [],
                "stable": [],
                "dropped": [],
                "gained": [],
            }

        if len(years) == 1:
            only_counter = yearly_counts[years[0]]
            ordered_keywords = self._sorted_keywords(only_counter)
            return {
                "author_id": author_id,
                "old_keywords": ordered_keywords,
                "new_keywords": ordered_keywords,
                "stable": ordered_keywords,
                "dropped": [],
                "gained": [],
            }

        window_size = max(window_years, 1)
        if len(years) >= window_size * 2:
            old_years = years[:window_size]
            new_years = years[-window_size:]
        else:
            midpoint = max(1, len(years) // 2)
            old_years = years[:midpoint]
            new_years = years[midpoint:] or years[-1:]

        old_counter = Counter()
        new_counter = Counter()
        for year in old_years:
            old_counter.update(yearly_counts[year])
        for year in new_years:
            new_counter.update(yearly_counts[year])

        old_keywords = self._sorted_keywords(old_counter)
        new_keywords = self._sorted_keywords(new_counter)
        old_set = set(old_keywords)
        new_set = set(new_keywords)

        stable = sorted(old_set & new_set)
        dropped = sorted(old_set - new_set)
        gained = sorted(new_set - old_set)

        return {
            "author_id": author_id,
            "old_keywords": old_keywords,
            "new_keywords": new_keywords,
            "stable": stable,
            "dropped": dropped,
            "gained": gained,
        }

    @staticmethod
    def _keyword_list(raw_keywords) -> list[str]:
        """Normalize JSONB keyword storage into a unique lowercase list."""
        if raw_keywords is None:
            return []

        if isinstance(raw_keywords, dict):
            if isinstance(raw_keywords.get("keywords"), list):
                items = raw_keywords["keywords"]
            else:
                items = list(raw_keywords.values())
        elif isinstance(raw_keywords, (list, tuple, set)):
            items = list(raw_keywords)
        else:
            return []

        keywords: list[str] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, dict):
                value = item.get("keyword") or item.get("name") or item.get("display_name")
            else:
                value = item
            if not isinstance(value, str):
                continue
            cleaned = value.strip().casefold()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            keywords.append(cleaned)
        return keywords

    @staticmethod
    def _sorted_keywords(counter: Counter[str]) -> list[str]:
        return [
            keyword
            for keyword, _ in sorted(
                counter.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]
"""Faceted filtering service — aggregated filter counts and multi-field queries.

Supports:
- Year range filtering
- Venue / journal filtering (with ranking)
- Author filtering
- Open access status filtering
- Paper type filtering
- Journal ranking filtering (SJR quartile, CCF rank, impact factor range)
- Keyword filtering
- Reproducibility signal filtering
"""

import structlog
from sqlalchemy import func, select, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.venue import Venue
from app.models.author import Author, PaperAuthor

logger = structlog.get_logger(__name__)


class FacetService:
    """Compute facet aggregations for the paper corpus."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_facets(
        self, fields: list[str], base_filter: dict | None = None
    ) -> dict[str, list[dict]]:
        """
        Get facet counts for requested fields.

        Args:
            fields: List of facet field names to aggregate.
            base_filter: Optional pre-filter to scope facets.

        Returns:
            {field: [{value, count}, ...]} for each requested field.
        """
        result = {}
        for field in fields:
            handler = getattr(self, f"_facet_{field}", None)
            if handler:
                result[field] = await handler(base_filter)
            else:
                logger.warning("unknown_facet_field", field=field)
        return result

    async def _facet_year(self, base_filter: dict | None) -> list[dict]:
        """Year distribution (grouped by year)."""
        query = (
            select(
                func.extract("year", Paper.published_at).label("year"),
                func.count(Paper.id).label("count"),
            )
            .where(Paper.deleted_at.is_(None), Paper.published_at.is_not(None))
            .group_by("year")
            .order_by(func.extract("year", Paper.published_at).desc())
            .limit(30)
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [
            {"value": int(r.year), "count": r.count}
            for r in rows.all() if r.year
        ]

    async def _facet_venue(self, base_filter: dict | None) -> list[dict]:
        """Venue distribution (top venues by paper count)."""
        query = (
            select(
                Venue.id,
                Venue.name,
                Venue.sjr_quartile,
                Venue.ccf_rank,
                func.count(Paper.id).label("count"),
            )
            .join(Paper, Paper.venue_id == Venue.id)
            .where(Paper.deleted_at.is_(None))
            .group_by(Venue.id, Venue.name, Venue.sjr_quartile, Venue.ccf_rank)
            .order_by(func.count(Paper.id).desc())
            .limit(50)
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [
            {
                "value": r.name,
                "count": r.count,
                "venue_id": str(r.id),
                "sjr_quartile": r.sjr_quartile,
                "ccf_rank": r.ccf_rank,
            }
            for r in rows.all()
        ]

    async def _facet_oa_status(self, base_filter: dict | None) -> list[dict]:
        """Open access status distribution."""
        query = (
            select(
                func.coalesce(Paper.oa_status, "unknown").label("status"),
                func.count(Paper.id).label("count"),
            )
            .where(Paper.deleted_at.is_(None))
            .group_by("status")
            .order_by(func.count(Paper.id).desc())
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [{"value": r.status, "count": r.count} for r in rows.all()]

    async def _facet_paper_type(self, base_filter: dict | None) -> list[dict]:
        """Paper type distribution (article, review, preprint, etc.)."""
        query = (
            select(
                func.coalesce(Paper.paper_type, "unknown").label("ptype"),
                func.count(Paper.id).label("count"),
            )
            .where(Paper.deleted_at.is_(None))
            .group_by("ptype")
            .order_by(func.count(Paper.id).desc())
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [{"value": r.ptype, "count": r.count} for r in rows.all()]

    async def _facet_language(self, base_filter: dict | None) -> list[dict]:
        """Language distribution."""
        query = (
            select(
                func.coalesce(Paper.language, "unknown").label("lang"),
                func.count(Paper.id).label("count"),
            )
            .where(Paper.deleted_at.is_(None))
            .group_by("lang")
            .order_by(func.count(Paper.id).desc())
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [{"value": r.lang, "count": r.count} for r in rows.all()]

    async def _facet_has_full_text(self, base_filter: dict | None) -> list[dict]:
        """Full-text availability."""
        query = (
            select(
                Paper.has_full_text.label("has_ft"),
                func.count(Paper.id).label("count"),
            )
            .where(Paper.deleted_at.is_(None))
            .group_by(Paper.has_full_text)
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [
            {"value": "yes" if r.has_ft else "no", "count": r.count}
            for r in rows.all()
        ]

    async def _facet_sjr_quartile(self, base_filter: dict | None) -> list[dict]:
        """SJR quartile distribution (Q1-Q4)."""
        query = (
            select(
                Venue.sjr_quartile.label("quartile"),
                func.count(Paper.id).label("count"),
            )
            .join(Paper, Paper.venue_id == Venue.id)
            .where(Paper.deleted_at.is_(None), Venue.sjr_quartile.is_not(None))
            .group_by(Venue.sjr_quartile)
            .order_by(Venue.sjr_quartile)
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [{"value": r.quartile, "count": r.count} for r in rows.all()]

    async def _facet_ccf_rank(self, base_filter: dict | None) -> list[dict]:
        """CCF rank distribution (A/B/C)."""
        query = (
            select(
                Venue.ccf_rank.label("rank"),
                func.count(Paper.id).label("count"),
            )
            .join(Paper, Paper.venue_id == Venue.id)
            .where(Paper.deleted_at.is_(None), Venue.ccf_rank.is_not(None))
            .group_by(Venue.ccf_rank)
            .order_by(Venue.ccf_rank)
        )
        query = self._apply_base_filter(query, base_filter)
        rows = await self.db.execute(query)
        return [{"value": r.rank, "count": r.count} for r in rows.all()]

    @staticmethod
    def _apply_base_filter(query, base_filter: dict | None):
        """Apply pre-filter conditions from a filter dict."""
        if not base_filter:
            return query
        if base_filter.get("year_from"):
            from datetime import date
            query = query.where(
                Paper.published_at >= date(base_filter["year_from"], 1, 1)
            )
        if base_filter.get("year_to"):
            from datetime import date
            query = query.where(
                Paper.published_at <= date(base_filter["year_to"], 12, 31)
            )
        if base_filter.get("oa_status"):
            query = query.where(Paper.oa_status == base_filter["oa_status"])
        if base_filter.get("has_full_text") is not None:
            query = query.where(
                Paper.has_full_text == base_filter["has_full_text"]
            )
        if base_filter.get("paper_type"):
            query = query.where(Paper.paper_type == base_filter["paper_type"])
        return query


class FilteredQueryService:
    """Build complex filtered + sorted paper queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def query_papers(
        self,
        filters: dict | None = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Query papers with rich filtering and sorting.

        Supported filters:
        - year_from, year_to: int
        - venue_ids: list[str]
        - author_ids: list[str]
        - oa_status: str ("gold", "green", "bronze", "closed")
        - paper_type: str
        - has_full_text: bool
        - sjr_quartile: list[str] ("Q1", "Q2", etc.)
        - ccf_rank: list[str] ("A", "B", "C")
        - impact_factor_min: float
        - min_citations: int
        - keywords: list[str]
        - language: str

        Supported sort_by:
        - published_at, citation_count, title, impact_factor
        """
        filters = filters or {}
        query = select(Paper).where(Paper.deleted_at.is_(None))
        count_query = (
            select(func.count(Paper.id)).where(Paper.deleted_at.is_(None))
        )

        # --- Apply filters ---
        if filters.get("year_from"):
            from datetime import date
            cond = Paper.published_at >= date(filters["year_from"], 1, 1)
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("year_to"):
            from datetime import date
            cond = Paper.published_at <= date(filters["year_to"], 12, 31)
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("oa_status"):
            cond = Paper.oa_status == filters["oa_status"]
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("paper_type"):
            cond = Paper.paper_type == filters["paper_type"]
            query = query.where(cond)
            count_query = count_query.where(cond)

        if "has_full_text" in filters:
            cond = Paper.has_full_text == filters["has_full_text"]
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("min_citations"):
            cond = Paper.citation_count >= filters["min_citations"]
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("language"):
            cond = Paper.language == filters["language"]
            query = query.where(cond)
            count_query = count_query.where(cond)

        if filters.get("keywords"):
            from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
            kw_conditions = [
                Paper.keywords.cast(PG_JSONB).contains([kw])
                for kw in filters["keywords"]
            ]
            kw_cond = or_(*kw_conditions)
            query = query.where(kw_cond)
            count_query = count_query.where(kw_cond)

        # Venue-based filters (require JOIN)
        needs_venue_join = any(
            filters.get(k)
            for k in ("venue_ids", "sjr_quartile", "ccf_rank", "impact_factor_min")
        )
        if needs_venue_join:
            query = query.join(Venue, Paper.venue_id == Venue.id)
            count_query = count_query.join(Venue, Paper.venue_id == Venue.id)

            if filters.get("venue_ids"):
                cond = Venue.id.in_(filters["venue_ids"])
                query = query.where(cond)
                count_query = count_query.where(cond)

            if filters.get("sjr_quartile"):
                cond = Venue.sjr_quartile.in_(filters["sjr_quartile"])
                query = query.where(cond)
                count_query = count_query.where(cond)

            if filters.get("ccf_rank"):
                cond = Venue.ccf_rank.in_(filters["ccf_rank"])
                query = query.where(cond)
                count_query = count_query.where(cond)

            if filters.get("impact_factor_min"):
                cond = Venue.impact_factor >= filters["impact_factor_min"]
                query = query.where(cond)
                count_query = count_query.where(cond)

        # Author-based filter (require JOIN)
        if filters.get("author_ids"):
            query = query.join(PaperAuthor, Paper.id == PaperAuthor.paper_id)
            count_query = count_query.join(
                PaperAuthor, Paper.id == PaperAuthor.paper_id
            )
            cond = PaperAuthor.author_id.in_(filters["author_ids"])
            query = query.where(cond)
            count_query = count_query.where(cond)

        # --- Sorting ---
        sort_col = {
            "published_at": Paper.published_at,
            "citation_count": Paper.citation_count,
            "title": Paper.title,
            "created_at": Paper.created_at,
        }.get(sort_by, Paper.published_at)

        if sort_order == "asc":
            query = query.order_by(sort_col.asc().nullslast())
        else:
            query = query.order_by(sort_col.desc().nullslast())

        # --- Count + paginate ---
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        papers = result.scalars().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "papers": [
                {
                    "id": str(p.id),
                    "doi": p.doi,
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "abstract": (p.abstract or "")[:300],
                    "published_at": str(p.published_at) if p.published_at else None,
                    "citation_count": p.citation_count,
                    "oa_status": p.oa_status,
                    "has_full_text": p.has_full_text,
                    "paper_type": p.paper_type,
                    "language": p.language,
                }
                for p in papers
            ],
        }

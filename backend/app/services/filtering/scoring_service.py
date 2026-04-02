"""Custom multi-factor paper scoring service.

Supports user-adjustable weights for:
- citations: Normalized citation count (log scale)
- recency: How recently published (exponential decay)
- relevance: Search relevance score (from upstream search)
- impact_factor: Venue impact factor (normalized)
- oa_bonus: Bonus for open access availability
- reproducibility: Has linked code/data
"""

import math
from datetime import date

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper
from app.models.venue import Venue

logger = structlog.get_logger(__name__)

# Default weights — user can override any of these
DEFAULT_WEIGHTS = {
    "citations": 0.25,
    "recency": 0.25,
    "relevance": 0.20,
    "impact_factor": 0.15,
    "oa_bonus": 0.10,
    "reproducibility": 0.05,
}


class ScoringService:
    """
    Multi-factor paper scoring with user-adjustable weights.

    Given a set of papers (from a filter query or search), compute
    a composite score = Σ(wi × fi) where wi is user weight and fi
    is the normalized factor value (0-1).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def score_papers(
        self,
        paper_ids: list[str],
        weights: dict[str, float] | None = None,
        relevance_scores: dict[str, float] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Score and rank papers by multi-factor weighted formula.

        Args:
            paper_ids: Papers to score (pre-filtered).
            weights: Factor weights (normalized internally). Defaults to DEFAULT_WEIGHTS.
            relevance_scores: Optional per-paper relevance scores from search.
            limit: Max results to return.

        Returns:
            Sorted list of {id, title, score, score_breakdown}.
        """
        w = dict(DEFAULT_WEIGHTS)
        if weights:
            w.update(weights)

        # Normalize weights to sum to 1.0
        total_w = sum(w.values())
        if total_w > 0:
            w = {k: v / total_w for k, v in w.items()}

        # Fetch papers with venue
        result = await self.db.execute(
            select(Paper)
            .where(Paper.id.in_(paper_ids), Paper.deleted_at.is_(None))
            .options(selectinload(Paper.venue))
        )
        papers = result.scalars().all()

        if not papers:
            return []

        # Compute normalization bounds
        max_citations = max((p.citation_count or 0 for p in papers), default=1) or 1
        today = date.today()

        relevance_scores = relevance_scores or {}

        scored = []
        for p in papers:
            breakdown = {}

            # Factor 1: Citation impact (log-normalized)
            raw_cite = p.citation_count or 0
            breakdown["citations"] = (
                math.log1p(raw_cite) / math.log1p(max_citations)
                if max_citations > 0
                else 0.0
            )

            # Factor 2: Recency (exponential decay, half-life = 2 years)
            if p.published_at:
                years_old = (today - p.published_at).days / 365.25
                breakdown["recency"] = math.exp(-0.35 * max(years_old, 0))
            else:
                breakdown["recency"] = 0.0

            # Factor 3: Search relevance (passed in from search results)
            breakdown["relevance"] = relevance_scores.get(str(p.id), 0.0)

            # Factor 4: Impact factor (log-normalized, 0-1)
            if p.venue and p.venue.impact_factor:
                # Impact factors range ~0-300; log-normalize
                breakdown["impact_factor"] = min(
                    math.log1p(p.venue.impact_factor) / math.log1p(100), 1.0
                )
            else:
                breakdown["impact_factor"] = 0.0

            # Factor 5: Open access bonus
            breakdown["oa_bonus"] = (
                1.0
                if p.oa_status in ("gold", "green", "diamond")
                else 0.5 if p.oa_status == "bronze" else 0.0
            )

            # Factor 6: Reproducibility signal
            breakdown["reproducibility"] = 1.0 if p.has_full_text else 0.0
            # TODO: Enhance with Papers With Code data and code availability

            # Weighted sum
            score = sum(w.get(k, 0) * v for k, v in breakdown.items())

            scored.append(
                {
                    "id": str(p.id),
                    "doi": p.doi,
                    "title": p.title,
                    "published_at": str(p.published_at) if p.published_at else None,
                    "citation_count": p.citation_count,
                    "score": round(score, 4),
                    "score_breakdown": {k: round(v, 4) for k, v in breakdown.items()},
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

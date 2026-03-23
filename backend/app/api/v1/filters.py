"""Advanced Filtering & Scoring API — faceted navigation and custom ranking.

P2 WS-1: §4 (#25-32) from FeasibilityAnalysis.md
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.filtering.facet_service import FacetService, FilteredQueryService
from app.services.filtering.scoring_service import ScoringService

router = APIRouter(prefix="/filters", tags=["filters"])


# ─── Schemas ─────────────────────────────────────────────────────

class FilterRequest(BaseModel):
    """Multi-field filter for paper queries."""
    year_from: int | None = None
    year_to: int | None = None
    venue_ids: list[str] | None = None
    author_ids: list[str] | None = None
    oa_status: str | None = None
    paper_type: str | None = None
    has_full_text: bool | None = None
    sjr_quartile: list[str] | None = None
    ccf_rank: list[str] | None = None
    impact_factor_min: float | None = None
    min_citations: int | None = None
    keywords: list[str] | None = None
    language: str | None = None


class ScoredListRequest(BaseModel):
    """Request for custom-scored paper list."""
    filters: FilterRequest = Field(default_factory=FilterRequest)
    weights: dict[str, float] | None = Field(
        None,
        description="Custom scoring weights. Keys: citations, recency, relevance, impact_factor, oa_bonus, reproducibility",
    )
    sort_by: str = Field("score", description="Sort field: score, published_at, citation_count, title")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# ─── Endpoints ───────────────────────────────────────────────────

@router.get("/facets")
async def get_facets(
    field: list[str] = Query(
        ...,
        description="Facet fields: year, venue, oa_status, paper_type, language, has_full_text, sjr_quartile, ccf_rank",
    ),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
    oa_status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated facet counts for the paper corpus.

    Returns grouped counts per requested field, useful for
    building filter UI (sidebar facets, checkboxes, sliders).
    """
    svc = FacetService(db)
    base_filter = {}
    if year_from:
        base_filter["year_from"] = year_from
    if year_to:
        base_filter["year_to"] = year_to
    if oa_status:
        base_filter["oa_status"] = oa_status

    facets = await svc.get_facets(field, base_filter or None)
    return {"facets": facets}


@router.post("/query")
async def query_papers(
    body: FilterRequest,
    sort_by: str = Query("published_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Query papers with multi-field filtering and sorting.

    Supports all filter fields: year range, venue, author, OA status,
    paper type, journal ranking (SJR/CCF/IF), citation threshold,
    keywords, language, full-text availability.
    """
    svc = FilteredQueryService(db)
    return await svc.query_papers(
        filters=body.model_dump(exclude_none=True),
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.post("/scored-list")
async def scored_paper_list(
    body: ScoredListRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get papers ranked by custom multi-factor scoring.

    score = w₁·citations + w₂·recency + w₃·relevance + w₄·impact_factor + w₅·oa_bonus + w₆·reproducibility

    All weights are user-adjustable and auto-normalized to sum=1.
    Default weights: {citations: 0.25, recency: 0.25, relevance: 0.20, impact_factor: 0.15, oa_bonus: 0.10, reproducibility: 0.05}
    """
    # First get filtered paper IDs
    filter_svc = FilteredQueryService(db)
    filtered = await filter_svc.query_papers(
        filters=body.filters.model_dump(exclude_none=True),
        limit=min(body.limit * 3, 500),  # Overfetch for scoring
        offset=body.offset,
    )

    paper_ids = [p["id"] for p in filtered["papers"]]
    if not paper_ids:
        return {"total": 0, "papers": []}

    # Then score them
    scoring_svc = ScoringService(db)
    scored = await scoring_svc.score_papers(
        paper_ids=paper_ids,
        weights=body.weights,
        limit=body.limit,
    )

    return {
        "total": filtered["total"],
        "papers": scored,
        "weights_used": body.weights or {},
    }

"""Researcher / Author Analytics API — §21 from FeasibilityAnalysis.md.

Provides:
- GET /researchers/emerging      — rising-star authors by citation velocity
- GET /researchers/{id}/profile  — full author profile with timeline
- GET /researchers/{id}/network  — ego co-authorship network (1-hop)
- GET /researchers/network       — global co-authorship network (top authors)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.analysis.researcher_service import ResearcherService
from app.services.enrichment.author_enrichment import AuthorEnrichmentService
from app.schemas.researchers import (
    AuthorProfileResponse,
    CollaborationNetworkResponse,
    EmergingAuthorsResponse,
)

router = APIRouter(prefix="/researchers", tags=["researchers"])


# ─── Emerging Authors ─────────────────────────────────────────────


@router.get("/emerging", response_model=EmergingAuthorsResponse)
async def emerging_authors(
    top_k: int = Query(20, ge=1, le=100, description="Number of authors to return"),
    recent_years: int = Query(
        2,
        ge=1,
        le=5,
        description="How many years back counts as 'emerging' (based on earliest library paper date)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Rising-star authors — earliest library paper within window, ranked by citation count.

    Identifies authors whose earliest publication in our library is within
    *recent_years*, sorted descending by total citation count. Useful for
    discovering early-career researchers whose work is already influential.

    Note: First publication date is computed from **published_at** on papers, not
    ingestion date. Pair with h_index and openalex_id for corroboration.
    """
    svc = ResearcherService(db)
    authors = await svc.emerging_authors(top_k=top_k, recent_years=recent_years)
    return EmergingAuthorsResponse(authors=authors)


# ─── Semantic Scholar Enrichment ──────────────────────────────────


@router.post("/{author_id}/enrich", summary="Enrich author from Semantic Scholar")
async def enrich_author(
    author_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch and persist author metadata from Semantic Scholar.

    Matching priority:
    1. Existing semantic_scholar_id → direct fetch
    2. ORCID match among search results
    3. Name + institution similarity (threshold 0.82)
    4. Name similarity alone (threshold 0.90)

    Returns the enriched fields and the match reason.
    Idempotent — safe to call multiple times.
    """
    svc = AuthorEnrichmentService(db)
    try:
        result = await svc.enrich(str(author_id))
    finally:
        await svc.close()

    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Author not found")
    return result


# ─── Author Profile ───────────────────────────────────────────────


@router.get("/{author_id}/profile", response_model=AuthorProfileResponse)
async def get_author_profile(
    # UUID type annotation causes FastAPI to validate and return 422 for malformed IDs
    author_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Full author profile including per-year publication timeline and top papers.

    Returns all papers for this author in the local library, not global stats.
    Use *openalex_id* in the response to fetch global statistics separately.
    """
    svc = ResearcherService(db)
    profile = await svc.get_author_profile(str(author_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Author not found")
    return AuthorProfileResponse(**profile)


# ─── Collaboration Networks ───────────────────────────────────────


@router.get("/{author_id}/network", response_model=CollaborationNetworkResponse)
async def author_ego_network(
    author_id: UUID,
    min_collaborations: int = Query(
        1,
        ge=1,
        le=20,
        description="Minimum shared papers to include an edge",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Co-authorship ego-network centered on a specific author.

    Returns all co-authors who have shared papers with this author in the
    local library, plus the edges between those co-authors (1-hop neighborhood).
    Edge weight = number of shared papers.
    """
    svc = ResearcherService(db)
    profile_check = await svc.get_author_profile(str(author_id))
    if not profile_check:
        raise HTTPException(status_code=404, detail="Author not found")

    network = await svc.collaboration_network(
        author_id=str(author_id),
        min_collaborations=min_collaborations,
    )
    return CollaborationNetworkResponse(**network)


@router.get("/network", response_model=CollaborationNetworkResponse)
async def global_network(
    top_k: int = Query(
        50,
        ge=5,
        le=200,
        description="How many top authors (by library paper count) to include as nodes",
    ),
    min_collaborations: int = Query(
        2,
        ge=1,
        le=20,
        description="Minimum shared papers to draw an edge",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Global co-authorship network over the most prolific library authors.

    All *top_k* authors are always returned as nodes. Edges are drawn
    only when two authors share ≥ *min_collaborations* papers. Authors
    with no qualifying edges appear as isolated nodes.
    Suitable for force-directed graph visualization.
    """
    svc = ResearcherService(db)
    network = await svc.collaboration_network(
        author_id=None,
        top_k=top_k,
        min_collaborations=min_collaborations,
    )
    return CollaborationNetworkResponse(**network)

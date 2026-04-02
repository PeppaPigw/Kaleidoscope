"""Graph API — citation graph queries, recommendations, and visualization data."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.graph.citation_graph import (
    CitationGraphService,
    RecommendationService,
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/papers/{paper_id}/citations")
async def get_paper_citations(
    paper_id: str,
    direction: str = Query("both", description="forward, backward, or both"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get citation relationships for a paper.

    - **forward**: Papers that cite this paper
    - **backward**: References this paper cites
    - **both**: Both directions
    """
    svc = CitationGraphService(db)
    return await svc.get_citations(paper_id, direction=direction, limit=limit)


@router.get("/papers/{paper_id}/co-citations")
async def co_citation_analysis(
    paper_id: str,
    limit: int = Query(20, le=100),
):
    """
    Co-citation analysis: papers frequently cited alongside this one.

    Co-citation count = number of papers that cite both target and result.
    Higher co-citation implies topical or methodological similarity.
    """
    svc = CitationGraphService()
    return await svc.co_citation_analysis(paper_id, limit=limit)


@router.get("/papers/{paper_id}/coupling")
async def bibliographic_coupling(
    paper_id: str,
    limit: int = Query(20, le=100),
):
    """
    Bibliographic coupling: papers citing the same references as this one.

    Shared references count = number of common reference targets.
    Higher coupling implies similar intellectual foundation.
    """
    svc = CitationGraphService()
    return await svc.bibliographic_coupling(paper_id, limit=limit)


@router.get("/papers/{paper_id}/similar")
async def recommend_similar(
    paper_id: str,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Recommend similar papers using multi-signal fusion.

    Combines bibliographic coupling + co-citation through
    Reciprocal Rank Fusion (RRF) for robust recommendations.
    """
    svc = RecommendationService(db)
    return await svc.recommend_similar(paper_id, limit=limit)


@router.get("/papers/{paper_id}/neighborhood")
async def get_graph_neighborhood(
    paper_id: str,
    depth: int = Query(1, ge=1, le=2),
    limit: int = Query(100, le=500),
):
    """
    Get graph neighborhood for visualization.

    Returns nodes and edges within `depth` hops for rendering
    with Cytoscape.js or D3.js on the frontend.
    """
    svc = CitationGraphService()
    return await svc.get_neighborhood(paper_id, depth=depth, limit=limit)


@router.post("/sync/{paper_id}")
async def sync_paper_to_graph(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger sync of a specific paper to Neo4j."""
    from sqlalchemy import select
    from app.models.paper import Paper

    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Paper not found")

    svc = CitationGraphService(db)
    return await svc.sync_paper(paper)


@router.post("/sync")
async def sync_all_papers(
    limit: int = Query(1000, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Batch-sync all papers to Neo4j graph."""
    svc = CitationGraphService(db)
    synced = await svc.sync_all_papers(limit=limit)
    return {"synced": synced}


@router.get("/stats")
async def graph_stats():
    """Get graph statistics (node/edge counts)."""
    svc = CitationGraphService()
    return await svc.get_stats()

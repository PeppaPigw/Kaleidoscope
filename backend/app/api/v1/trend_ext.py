"""Extended trends API — topic evolution, experts, venues, and direction shifts."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.analysis.trend_extensions import TrendExtensionsService

router = APIRouter(prefix="/trends/ext", tags=["trends"])


@router.get("/topic-evolution")
async def get_topic_evolution(
    top_keywords: int = Query(10, ge=1, le=50),
    start_year: int = Query(2010, ge=1900),
    db: AsyncSession = Depends(get_db),
):
    """Return yearly counts for the most frequent keywords."""
    svc = TrendExtensionsService(db)
    return await svc.get_topic_evolution(
        top_keywords=top_keywords,
        start_year=start_year,
    )


@router.get("/expert-finder")
async def get_expert_finder(
    keywords: list[str] = Query([]),
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Find authors whose papers match all requested keywords."""
    svc = TrendExtensionsService(db)
    return await svc.get_expert_finder(keywords=keywords, top_k=top_k)


@router.get("/venue-ranking")
async def get_venue_ranking(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Rank venues by citation performance."""
    svc = TrendExtensionsService(db)
    return await svc.get_venue_ranking(limit=limit)


@router.get("/author/{author_id}/direction-change")
async def get_researcher_direction_change(
    author_id: UUID,
    window_years: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Compare older vs newer keyword windows for a researcher."""
    svc = TrendExtensionsService(db)
    return await svc.get_researcher_direction_change(
        author_id=str(author_id),
        window_years=window_years,
    )

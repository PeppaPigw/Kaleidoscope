"""Trend & Topic Analysis API — topics, hot keywords, emerging entities.

P2 WS-2: §10 (#73-80) from FeasibilityAnalysis.md
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.analysis.trend_service import TopicService, TrendService

router = APIRouter(prefix="/trends", tags=["trends"])


# ─── Topics ──────────────────────────────────────────────────────

@router.get("/topics")
async def list_topics(
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("paper_count", description="paper_count, label, trend"),
    db: AsyncSession = Depends(get_db),
):
    """List discovered research topics with paper counts and trend direction."""
    svc = TopicService(db)
    return {"topics": await svc.list_topics(limit=limit, sort_by=sort_by)}


@router.get("/topics/{topic_id}")
async def get_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get topic detail with keywords and representative papers."""
    svc = TopicService(db)
    topic = await svc.get_topic(topic_id)
    if not topic:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics/refresh")
async def refresh_topics(
    db: AsyncSession = Depends(get_db),
):
    """
    Re-run BERTopic clustering on all paper abstracts (admin).

    This is computationally expensive and should be run sparingly.
    Requires at least 20 papers with abstracts.
    """
    svc = TopicService(db)
    return await svc.refresh_topics()


# ─── Keywords & Trends ───────────────────────────────────────────

@router.get("/hot-keywords")
async def hot_keywords(
    top_k: int = Query(30, ge=1, le=100),
    years_back: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Discover hot keywords by frequency growth rate.

    Ranks keywords by year-over-year growth in paper count.
    Includes per-year breakdown and trend direction.
    """
    svc = TrendService(db)
    return {"keywords": await svc.hot_keywords(top_k=top_k, years_back=years_back)}


# ─── Emerging Entities ───────────────────────────────────────────

@router.get("/emerging-authors")
async def emerging_authors(
    top_k: int = Query(20, ge=1, le=100),
    recent_years: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
):
    """
    Find emerging researchers with high-impact recent publications.

    Identifies authors whose first publication is within the last N years,
    ranked by total citation count.
    """
    svc = TrendService(db)
    return {"authors": await svc.emerging_authors(top_k=top_k, recent_years=recent_years)}


@router.get("/sleeping-beauties")
async def sleeping_beauties(
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Find 'sleeping beauty' papers: old papers gaining recent attention.

    Identifies papers published >5 years ago with unusually high
    citation counts relative to their age.
    """
    svc = TrendService(db)
    return {"papers": await svc.sleeping_beauties(top_k=top_k)}

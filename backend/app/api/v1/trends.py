"""Trend & Topic Analysis API — topics, hot keywords, emerging entities.

P2 WS-2: §10 (#73-80) from FeasibilityAnalysis.md
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.trends import (
    HotKeywordsResponse,
    KeywordCooccurrenceResponse,
    KeywordTimeseriesResponse,
    SleepingPapersResponse,
    TopicDetailResponse,
    TopicsResponse,
)
from app.services.analysis.trend_service import TopicService, TrendService

router = APIRouter(prefix="/trends", tags=["trends"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Topics ──────────────────────────────────────────────────────


@router.get("/topics", response_model=TopicsResponse)
async def list_topics(
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("paper_count", description="paper_count, label, trend"),
):
    """List discovered research topics with paper counts and trend direction."""
    svc = TopicService(db)
    topics = await svc.list_topics(limit=limit, sort_by=sort_by)
    return TopicsResponse(topics=topics)


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: str,
    db: DbSession,
):
    """Get topic detail with keywords and representative papers."""
    svc = TopicService(db)
    topic = await svc.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics/refresh")
async def refresh_topics(
    db: DbSession,
):
    """
    Re-run BERTopic clustering on all paper abstracts (admin).

    This is computationally expensive and should be run sparingly.
    Requires at least 20 papers with abstracts.
    """
    svc = TopicService(db)
    return await svc.refresh_topics()


# ─── Keywords & Trends ───────────────────────────────────────────


@router.get("/hot-keywords", response_model=HotKeywordsResponse)
async def hot_keywords(
    db: DbSession,
    top_k: int | None = Query(None, ge=1, le=100),
    limit: int | None = Query(None, ge=1, le=100),
    years_back: int = Query(3, ge=1, le=10),
):
    """
    Discover hot keywords by frequency growth rate.

    Ranks keywords by year-over-year growth in paper count.
    Includes per-year breakdown and trend direction.
    """
    svc = TrendService(db)
    resolved_top_k = top_k if top_k is not None else limit if limit is not None else 30
    keywords = await svc.hot_keywords(top_k=resolved_top_k, years_back=years_back)
    return HotKeywordsResponse(keywords=keywords)


@router.get("/keywords/timeseries", response_model=KeywordTimeseriesResponse)
async def keyword_timeseries(
    db: DbSession,
    keywords: str = Query(..., description="Comma-separated keywords to track"),
    years_back: int = Query(5, ge=1, le=15),
):
    """
    Year-by-year paper counts for specific keywords.

    Pass multiple keywords as comma-separated list to compare trends.
    Example: ?keywords=transformer,attention,BERT
    """
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        raise HTTPException(status_code=422, detail="At least one keyword required")
    if len(kw_list) > 10:
        raise HTTPException(status_code=422, detail="Maximum 10 keywords per request")
    svc = TrendService(db)
    result = await svc.keyword_timeseries(keywords=kw_list, years_back=years_back)
    return KeywordTimeseriesResponse(**result)


@router.get("/keywords/cooccurrence", response_model=KeywordCooccurrenceResponse)
async def keyword_cooccurrence(
    db: DbSession,
    top_keywords: int = Query(
        30, ge=5, le=100, description="Top N keywords to include"
    ),
    years_back: int = Query(3, ge=1, le=10),
    min_cooccurrence: int = Query(2, ge=1, le=50),
):
    """
    Keyword co-occurrence graph edges.

    Returns pairs of keywords that appear together in papers,
    sorted by co-occurrence count. Useful for thematic bridging discovery (§79).
    """
    svc = TrendService(db)
    result = await svc.keyword_cooccurrence(
        top_keywords=top_keywords,
        years_back=years_back,
        min_cooccurrence=min_cooccurrence,
    )
    return KeywordCooccurrenceResponse(**result)


# ─── Emerging Entities (Deprecated — use /researchers/emerging) ──


@router.get(
    "/emerging-authors",
    deprecated=True,
    summary="[Deprecated] Use GET /researchers/emerging instead",
)
async def emerging_authors(
    db: DbSession,
    top_k: int = Query(20, ge=1, le=100),
    recent_years: int = Query(2, ge=1, le=5),
):
    """
    **Deprecated** — use `GET /api/v1/researchers/emerging` for the canonical,
    typed response and richer author profile data.

    This endpoint delegates to the same ResearcherService implementation.
    """
    from app.services.analysis.researcher_service import ResearcherService

    svc = ResearcherService(db)
    return {
        "authors": await svc.emerging_authors(top_k=top_k, recent_years=recent_years)
    }


# ─── Sleeping Papers ─────────────────────────────────────────────


@router.get("/sleeping-papers", response_model=SleepingPapersResponse)
async def sleeping_papers(
    db: DbSession,
    top_k: int = Query(10, ge=1, le=50),
):
    """
    Find 'sleeping beauty' papers: old papers gaining recent attention.

    Identifies papers published >5 years ago, ranked by proxy score
    (citation_count / sqrt(years_old)). High proxy score = high impact
    relative to age.
    """
    svc = TrendService(db)
    papers = await svc.sleeping_beauties(top_k=top_k)
    return SleepingPapersResponse(papers=papers)


@router.get("/sleeping-beauties", response_model=SleepingPapersResponse)
async def sleeping_beauties_alias(
    db: DbSession,
    top_k: int = Query(10, ge=1, le=50),
):
    """Alias for /sleeping-papers (backward compatibility)."""
    svc = TrendService(db)
    papers = await svc.sleeping_beauties(top_k=top_k)
    return SleepingPapersResponse(papers=papers)

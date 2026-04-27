"""RSS Feed management API routes."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.feed import RSSFeed
from app.schemas.feed import (
    PollResult,
    RSSFeedCreate,
    RSSFeedListResponse,
    RSSFeedResponse,
)
from app.tasks.ingest_tasks import poll_rss_feeds

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.get("", response_model=RSSFeedListResponse)
async def list_feeds(
    db: AsyncSession = Depends(get_db),
):
    """List all RSS feed subscriptions."""
    result = await db.execute(select(RSSFeed).order_by(RSSFeed.name))
    feeds = result.scalars().all()

    return RSSFeedListResponse(
        items=[
            RSSFeedResponse(
                id=f.id,
                url=f.url,
                name=f.name,
                publisher=f.publisher,
                category=f.category,
                is_active=f.is_active,
                last_polled_at=f.last_polled_at,
                poll_error_count=f.poll_error_count,
                total_items_discovered=f.total_items_discovered,
                pdf_capability=f.pdf_capability,
                created_at=f.created_at,
            )
            for f in feeds
        ],
        total=len(feeds),
    )


@router.post("", response_model=RSSFeedResponse, status_code=201)
async def create_feed(
    request: RSSFeedCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new RSS feed subscription."""
    # Check for duplicate URL
    existing = await db.execute(select(RSSFeed).where(RSSFeed.url == request.url))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "FEED_EXISTS",
                "message": f"Feed URL already exists: {request.url}",
            },
        )

    feed = RSSFeed(
        url=request.url,
        name=request.name,
        publisher=request.publisher,
        category=request.category,
        pdf_capability=request.pdf_capability,
    )
    db.add(feed)
    await db.flush()

    return RSSFeedResponse(
        id=feed.id,
        url=feed.url,
        name=feed.name,
        publisher=feed.publisher,
        category=feed.category,
        is_active=feed.is_active,
        last_polled_at=feed.last_polled_at,
        poll_error_count=feed.poll_error_count,
        total_items_discovered=feed.total_items_discovered,
        pdf_capability=feed.pdf_capability,
        created_at=feed.created_at,
    )


@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an RSS feed subscription."""
    result = await db.execute(select(RSSFeed).where(RSSFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(
            status_code=404,
            detail={"code": "FEED_NOT_FOUND", "message": f"Feed {feed_id} not found"},
        )

    await db.delete(feed)
    return {"status": "deleted", "feed_id": str(feed_id)}


@router.post("/poll", response_model=PollResult)
async def trigger_poll(
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger polling of all active RSS feeds."""
    task = poll_rss_feeds.delay()
    return PollResult(
        feeds_polled=0,
        new_papers_discovered=0,
        errors=0,
        details=[{"message": f"Poll task queued. Task ID: {task.id}"}],
    )

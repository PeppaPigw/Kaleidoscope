"""Pydantic schemas for RSS Feed management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RSSFeedCreate(BaseModel):
    """Create a new RSS feed subscription."""

    url: str = Field(..., description="RSS feed URL")
    name: str = Field(..., max_length=200)
    publisher: str | None = None
    category: str | None = None
    pdf_capability: str | None = Field(
        None, description="direct, unpaywall, tdm, metadata_only"
    )


class RSSFeedResponse(BaseModel):
    """RSS feed details."""

    id: uuid.UUID
    url: str
    name: str
    publisher: str | None = None
    category: str | None = None
    is_active: bool
    last_polled_at: datetime | None = None
    poll_error_count: int
    total_items_discovered: int
    pdf_capability: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RSSFeedListResponse(BaseModel):
    """List of RSS feeds."""

    items: list[RSSFeedResponse]
    total: int


class PollResult(BaseModel):
    """Result of polling RSS feeds."""

    feeds_polled: int
    new_papers_discovered: int
    errors: int
    details: list[dict] = []

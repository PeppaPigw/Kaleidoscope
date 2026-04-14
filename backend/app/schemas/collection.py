"""Pydantic schemas for Collections, Tags, and reading status."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ─── Tags ────────────────────────────────────────────────────────────


class TagCreate(BaseModel):
    """Create a new tag."""

    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: str | None = None


class TagUpdate(BaseModel):
    """Update a tag."""

    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: str | None = None


class TagResponse(BaseModel):
    """Tag in API responses."""

    id: uuid.UUID
    name: str
    color: str | None
    description: str | None
    paper_count: int = 0

    model_config = {"from_attributes": True}


# ─── Collections ─────────────────────────────────────────────────────

CollectionKind = Literal["workspace", "subscription_collection", "paper_group"]


class CollectionCreate(BaseModel):
    """Create a new collection."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    kind: CollectionKind = "workspace"
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = None
    parent_collection_id: uuid.UUID | None = None
    is_smart: bool = False
    smart_filter: dict | None = None


class CollectionUpdate(BaseModel):
    """Update a collection."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    kind: CollectionKind | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = None
    parent_collection_id: uuid.UUID | None = None
    smart_filter: dict | None = None


class CollectionPaperAdd(BaseModel):
    """Add paper(s) to a collection."""

    paper_ids: list[uuid.UUID] = Field(..., min_length=1)
    note: str | None = None


class CollectionPaperReorder(BaseModel):
    """Reorder papers in a collection."""

    paper_ids: list[uuid.UUID] = Field(..., description="Paper IDs in desired order")


class CollectionPaperResponse(BaseModel):
    """Paper within a collection."""

    paper_id: uuid.UUID
    position: int
    note: str | None
    added_at: datetime
    # Inline paper summary fields
    title: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    published_at: datetime | None = None
    reading_status: str | None = None

    model_config = {"from_attributes": True}


class CollectionResponse(BaseModel):
    """Collection in API responses (list view)."""

    id: uuid.UUID
    name: str
    description: str | None
    kind: CollectionKind = "workspace"
    color: str | None
    icon: str | None
    parent_collection_id: uuid.UUID | None = None
    is_smart: bool
    paper_count: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CollectionDetailResponse(CollectionResponse):
    """Collection with papers (detail view)."""

    smart_filter: dict | None = None
    papers: list[CollectionPaperResponse] = []


class CollectionFeedSubscriptionCreate(BaseModel):
    """Attach feeds to a subscription collection."""

    feed_ids: list[uuid.UUID] = Field(..., min_length=1)


class CollectionFeedSubscriptionResponse(BaseModel):
    """Feed attached to a collection."""

    id: uuid.UUID
    feed_id: uuid.UUID
    collection_id: uuid.UUID
    feed_name: str | None = None
    publisher: str | None = None
    category: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CollectionChatThreadCreate(BaseModel):
    """Create a new thread under a collection."""

    title: str | None = Field(None, max_length=255)


class CollectionChatThreadResponse(BaseModel):
    """Collection-scoped chat thread summary."""

    id: uuid.UUID
    collection_id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CollectionChatMessageAsk(BaseModel):
    """Persist a user message and request an assistant answer."""

    content: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)


class CollectionChatMessageResponse(BaseModel):
    """Collection chat message payload."""

    id: uuid.UUID
    thread_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    content: str
    sources: dict | None = None
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Reading Status ──────────────────────────────────────────────────


class ReadingStatusUpdate(BaseModel):
    """Update paper reading status."""

    status: Literal["unread", "to_read", "reading", "read", "archived"]


# ─── Citation Export ─────────────────────────────────────────────────


class ExportRequest(BaseModel):
    """Request citation export for paper(s)."""

    paper_ids: list[uuid.UUID] | None = Field(
        None, description="Specific papers. Omit to export all in collection."
    )
    format: Literal["bibtex", "ris", "csl_json"] = "bibtex"

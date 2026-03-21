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

class CollectionCreate(BaseModel):
    """Create a new collection."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = None
    is_smart: bool = False
    smart_filter: dict | None = None


class CollectionUpdate(BaseModel):
    """Update a collection."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = None
    smart_filter: dict | None = None


class CollectionPaperAdd(BaseModel):
    """Add paper(s) to a collection."""
    paper_ids: list[uuid.UUID] = Field(..., min_length=1)
    note: str | None = None


class CollectionPaperReorder(BaseModel):
    """Reorder papers in a collection."""
    paper_ids: list[uuid.UUID] = Field(
        ..., description="Paper IDs in desired order"
    )


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
    color: str | None
    icon: str | None
    is_smart: bool
    paper_count: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CollectionDetailResponse(CollectionResponse):
    """Collection with papers (detail view)."""
    smart_filter: dict | None = None
    papers: list[CollectionPaperResponse] = []


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

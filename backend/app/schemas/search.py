"""Pydantic schemas for Search API."""

import uuid
from datetime import date

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search query parameters."""

    query: str = Field(..., min_length=1, max_length=500)
    mode: str = Field("hybrid", description="Search mode: keyword, semantic, hybrid")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    # Optional filters
    year_from: int | None = None
    year_to: int | None = None
    venue: str | None = None
    paper_type: str | None = None
    oa_status: str | None = None
    has_full_text: bool | None = None

    # Sort
    sort_by: str = Field(
        "relevance", description="relevance, year, citation_count, created_at"
    )
    order: str = Field("desc", description="asc or desc")


class SearchHit(BaseModel):
    """A single search result."""

    paper_id: uuid.UUID
    doi: str | None = None
    arxiv_id: str | None = None
    title: str
    title_zh: str | None = None
    abstract: str | None = None
    abstract_zh: str | None = None
    published_at: date | None = None
    citation_count: int | None = None
    authors: list[str] = []
    venue: str | None = None
    score: float  # Relevance score
    highlights: dict[str, list[str]] | None = None  # {field: [highlighted_snippet]}

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    """Search results with pagination."""

    hits: list[SearchHit]
    total: int
    page: int
    per_page: int
    query: str
    mode: str
    mode_used: str | None = None
    processing_time_ms: float

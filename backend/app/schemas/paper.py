"""Pydantic schemas for Paper API requests and responses."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# --- Request Schemas ---


class PaperImportRequest(BaseModel):
    """Import a single paper by identifier."""

    identifier: str = Field(..., description="DOI, arXiv ID, PMID, or URL")
    identifier_type: Literal["doi", "arxiv", "pmid", "url", "title"] = Field(
        ..., description="Type of identifier: doi, arxiv, pmid, url, title"
    )


class PaperBatchImportRequest(BaseModel):
    """Import multiple papers."""

    items: list[PaperImportRequest] = Field(..., max_length=100)


# --- Response Schemas ---


class ProvenanceInfo(BaseModel):
    """Provenance metadata for an AI-derived field."""

    source: str
    timestamp: datetime | None = None
    confidence: float | None = None


class AuthorBrief(BaseModel):
    """Brief author info for paper list views."""

    id: uuid.UUID
    display_name: str
    position: int
    is_corresponding: bool = False


class VenueBrief(BaseModel):
    """Brief venue info for paper responses."""

    id: uuid.UUID
    name: str
    type: str | None = None


class PaperResponse(BaseModel):
    """Full paper response with all metadata."""

    # Per-user reading status is intentionally excluded here; use the
    # UserReadingStatus-backed /papers/{id}/reading-status endpoint instead.
    id: uuid.UUID
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    title: str
    title_zh: str | None = None
    abstract: str | None = None
    abstract_zh: str | None = None
    published_at: date | None = None
    paper_type: str | None = None
    oa_status: str | None = None
    language: str | None = None
    keywords: list[str] | None = None
    citation_count: int | None = None
    has_full_text: bool = False
    ingestion_status: str
    summary: str | None = None
    highlights: list[str] | None = None
    contributions: list[str] | None = None
    limitations: list[str] | None = None
    paper_labels: dict | None = None
    authors: list[AuthorBrief] = []
    venue: str | None = None
    raw_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PaperBriefResponse(BaseModel):
    """Compact paper response for list views."""

    id: uuid.UUID
    doi: str | None = None
    arxiv_id: str | None = None
    title: str
    title_zh: str | None = None
    abstract: str | None = None
    abstract_zh: str | None = None
    published_at: date | None = None
    citation_count: int | None = None
    has_full_text: bool = False
    ingestion_status: str
    paper_labels: dict | None = None
    authors: list[AuthorBrief] = []
    venue: VenueBrief | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperListResponse(BaseModel):
    """Paginated list of papers."""

    items: list[PaperBriefResponse]
    total: int
    page: int
    per_page: int


class ImportResult(BaseModel):
    """Result of a paper import operation."""

    paper_id: uuid.UUID | None = None
    identifier: str
    status: str  # created, duplicate, queued, failed
    message: str | None = None


class BatchImportResult(BaseModel):
    """Result of a batch import."""

    results: list[ImportResult]
    total: int
    created: int
    duplicates: int
    queued: int
    failed: int

"""Pydantic schemas for persisted writing documents."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WritingDocumentUpdateRequest(BaseModel):
    """Update a writing document title and/or markdown body."""

    title: str | None = Field(None, min_length=1, max_length=255)
    markdown_content: str | None = None


class WritingDocumentResponse(BaseModel):
    """Writing document in API responses."""

    id: uuid.UUID
    user_id: str
    title: str
    markdown_content: str
    plain_text_excerpt: str
    word_count: int
    cover_image_url: str | None
    last_opened_at: datetime | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WritingDocumentListResponse(BaseModel):
    """User-scoped writing document list."""

    items: list[WritingDocumentResponse]
    total: int


class WritingImageUploadResponse(BaseModel):
    """Uploaded writing image metadata."""

    url: str

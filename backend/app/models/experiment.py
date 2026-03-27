"""Experiment & Method models — first-class research entities (§14 ext).

Captures structured experiment designs, method descriptions,
and dataset references extracted from papers or created by users.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class Experiment(UUIDPrimaryKeyMixin, Base):
    """A reproducible experiment extracted from or linked to a paper."""

    __tablename__ = "experiments"

    paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Structured fields
    setup: Mapped[dict | None] = mapped_column(JSONB)
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    results: Mapped[dict | None] = mapped_column(JSONB)
    metrics: Mapped[dict | None] = mapped_column(JSONB)
    # Provenance
    source: Mapped[str | None] = mapped_column(
        String(50)
    )  # extracted | manual | imported
    status: Mapped[str] = mapped_column(
        String(30), default="draft"
    )  # draft | validated | reproduced | failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class Method(UUIDPrimaryKeyMixin, Base):
    """A research method/technique referenced in papers."""

    __tablename__ = "methods"

    name: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    # Structured parameters
    typical_params: Mapped[dict | None] = mapped_column(JSONB)
    # How many papers use this method
    paper_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Dataset(UUIDPrimaryKeyMixin, Base):
    """A dataset referenced in papers."""

    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(100))
    size_description: Mapped[str | None] = mapped_column(String(255))
    license: Mapped[str | None] = mapped_column(String(100))
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB)
    paper_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

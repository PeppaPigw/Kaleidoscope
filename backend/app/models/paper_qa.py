"""ORM models for Paper QA — chunks, embedding jobs, and QA messages."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, ForeignKey
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PaperChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A section-level chunk of a paper with its embedding vector."""

    __tablename__ = "paper_chunks"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_section_title: Mapped[str] = mapped_column(String(100), nullable=False)
    section_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_appendix: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_references: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_paper_chunks_paper_order", "paper_id", "order_index"),
    )


class PaperEmbeddingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks the embedding pipeline status for a paper."""

    __tablename__ = "paper_embedding_jobs"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending / running / completed / failed
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (UniqueConstraint("paper_id", name="uq_paper_embedding_jobs_paper_id"),)


class QAMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single Q&A exchange for a paper."""

    __tablename__ = "qa_messages"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

"""Paper model — central entity of Kaleidoscope."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.author import PaperAuthor
    from app.models.collection import PaperTag
    from app.models.venue import Venue


class Paper(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Central paper entity.

    Stores metadata, provenance, and links to PDF/full-text.
    AI-derived fields have companion `_provenance` JSONB columns.
    """

    __tablename__ = "papers"

    # --- Identifiers ---
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(50), index=True)
    pmid: Mapped[str | None] = mapped_column(String(20), index=True)
    openalex_id: Mapped[str | None] = mapped_column(String(50), index=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # --- Core Metadata ---
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[date | None] = mapped_column(Date, index=True)
    paper_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # article, review, preprint, etc.
    language: Mapped[str | None] = mapped_column(String(10), default="en")
    keywords: Mapped[list | None] = mapped_column(JSONB)  # ["quantum", "ML"]

    # --- Venue ---
    venue_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True
    )
    venue: Mapped[Venue | None] = relationship("Venue", back_populates="papers")
    volume: Mapped[str | None] = mapped_column(String(50))
    issue: Mapped[str | None] = mapped_column(String(50))
    pages: Mapped[str | None] = mapped_column(String(50))

    # --- Open Access ---
    oa_status: Mapped[str | None] = mapped_column(
        String(20)
    )  # gold, green, bronze, closed
    license: Mapped[str | None] = mapped_column(String(100))

    # --- Citation Metrics ---
    citation_count: Mapped[int | None] = mapped_column(Integer, default=0)
    influential_citation_count: Mapped[int | None] = mapped_column(Integer)
    citation_count_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # --- Full-text & Storage ---
    pdf_path: Mapped[str | None] = mapped_column(Text)  # MinIO object key
    remote_urls: Mapped[list | None] = mapped_column(
        JSONB
    )  # [{url, source, type}]
    has_full_text: Mapped[bool] = mapped_column(default=False)

    # --- Markdown Content (primary storage format) ---
    full_text_markdown: Mapped[str | None] = mapped_column(Text)
    markdown_provenance: Mapped[dict | None] = mapped_column(JSONB)
    # {source: "mineru", model_version: "vlm", timestamp: "...", batch_id: "..."}

    # --- Raw Data ---
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)  # Original API response
    grobid_tei: Mapped[str | None] = mapped_column(Text)  # GROBID TEI XML output

    # --- Processing State ---
    ingestion_status: Mapped[str] = mapped_column(
        String(20), default="discovered"
    )  # discovered, enriched, pdf_acquired, parsed, indexed, failed
    parser_version: Mapped[str | None] = mapped_column(String(20))
    ingestion_error: Mapped[str | None] = mapped_column(Text)

    # --- Reading Status (Legacy) ---
    # Deprecated paper-level status retained for backward compatibility only.
    # Canonical per-user status lives in UserReadingStatus and is exposed via
    # /api/v1/papers/{id}/reading-status.
    reading_status: Mapped[str] = mapped_column(
        String(20), default="unread"
    )  # unread, to_read, reading, read, archived

    # --- AI-Derived Fields + Provenance ---
    summary: Mapped[str | None] = mapped_column(Text)
    summary_provenance: Mapped[dict | None] = mapped_column(JSONB)
    # {source: "gpt-4o", timestamp: "...", confidence: 0.92}

    highlights: Mapped[list | None] = mapped_column(JSONB)  # [str]
    highlights_provenance: Mapped[dict | None] = mapped_column(JSONB)

    contributions: Mapped[list | None] = mapped_column(JSONB)  # [str]
    contributions_provenance: Mapped[dict | None] = mapped_column(JSONB)

    limitations: Mapped[list | None] = mapped_column(JSONB)  # [str]
    limitations_provenance: Mapped[dict | None] = mapped_column(JSONB)

    # --- P2: Local PDF & Analysis ---
    visibility: Mapped[str] = mapped_column(
        String(20), default="private"
    )  # private, shared, public
    source_type: Mapped[str] = mapped_column(
        String(20), default="remote"
    )  # remote, local_upload, local_folder
    local_annotations: Mapped[list | None] = mapped_column(JSONB)
    parsed_sections: Mapped[list | None] = mapped_column(JSONB)
    # [{title, paragraphs, level}] — structured sections
    parsed_figures: Mapped[list | None] = mapped_column(JSONB)
    # [{label, caption, type, page}] — extracted figure/table metadata

    # --- Relationships ---
    authors: Mapped[list[PaperAuthor]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )
    versions: Mapped[list[PaperVersion]] = relationship(
        "PaperVersion", back_populates="paper", cascade="all, delete-orphan"
    )
    references: Mapped[list[PaperReference]] = relationship(
        "PaperReference",
        back_populates="citing_paper",
        foreign_keys="PaperReference.citing_paper_id",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[PaperTag]] = relationship(
        "PaperTag", cascade="all, delete-orphan", overlaps="paper",
    )

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, doi={self.doi}, title={self.title[:50]}...)>"


class PaperVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track different versions of a paper (e.g., arXiv v1, v2, published)."""

    __tablename__ = "paper_versions"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    arxiv_version: Mapped[str | None] = mapped_column(String(10))  # "v1", "v2"
    source_url: Mapped[str | None] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(default=True)

    paper: Mapped[Paper] = relationship("Paper", back_populates="versions")


class PaperReference(UUIDPrimaryKeyMixin, Base):
    """Citation relationship between papers, extracted from reference lists."""

    __tablename__ = "paper_references"

    citing_paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    cited_paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True, index=True
    )  # Null if cited paper not in DB

    # Raw reference data (from GROBID)
    raw_title: Mapped[str | None] = mapped_column(Text)
    raw_authors: Mapped[str | None] = mapped_column(Text)
    raw_year: Mapped[str | None] = mapped_column(String(10))
    raw_doi: Mapped[str | None] = mapped_column(String(255))
    raw_string: Mapped[str | None] = mapped_column(Text)  # Full reference string
    position: Mapped[int | None] = mapped_column(Integer)  # Order in reference list

    citing_paper: Mapped[Paper] = relationship(
        "Paper", back_populates="references", foreign_keys=[citing_paper_id]
    )
    cited_paper: Mapped[Paper | None] = relationship(
        "Paper", foreign_keys=[cited_paper_id]
    )


class MetadataProvenance(UUIDPrimaryKeyMixin, Base):
    """Source trace for individual paper metadata fields (§15).

    Each row records where a specific field value was obtained,
    enabling transparent audit trails and trust scoring.
    """

    __tablename__ = "metadata_provenance"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

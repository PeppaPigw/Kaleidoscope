"""Paper model — central entity of Kaleidoscope."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


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
    keywords: Mapped[dict | None] = mapped_column(JSONB)  # ["quantum", "ML"]

    # --- Venue ---
    venue_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True
    )
    venue: Mapped["Venue | None"] = relationship("Venue", back_populates="papers")
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
    remote_urls: Mapped[dict | None] = mapped_column(
        JSONB
    )  # [{url, source, type}]
    has_full_text: Mapped[bool] = mapped_column(default=False)

    # --- Raw Data ---
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)  # Original API response
    grobid_tei: Mapped[str | None] = mapped_column(Text)  # GROBID TEI XML output

    # --- Processing State ---
    ingestion_status: Mapped[str] = mapped_column(
        String(20), default="discovered"
    )  # discovered, enriched, pdf_acquired, parsed, indexed, failed
    parser_version: Mapped[str | None] = mapped_column(String(20))
    ingestion_error: Mapped[str | None] = mapped_column(Text)

    # --- Reading Status (P1) ---
    reading_status: Mapped[str] = mapped_column(
        String(20), default="unread"
    )  # unread, to_read, reading, read, archived

    # --- AI-Derived Fields + Provenance ---
    summary: Mapped[str | None] = mapped_column(Text)
    summary_provenance: Mapped[dict | None] = mapped_column(JSONB)
    # {source: "gpt-4o", timestamp: "...", confidence: 0.92}

    highlights: Mapped[dict | None] = mapped_column(JSONB)  # [str]
    highlights_provenance: Mapped[dict | None] = mapped_column(JSONB)

    contributions: Mapped[dict | None] = mapped_column(JSONB)  # [str]
    contributions_provenance: Mapped[dict | None] = mapped_column(JSONB)

    limitations: Mapped[dict | None] = mapped_column(JSONB)  # [str]
    limitations_provenance: Mapped[dict | None] = mapped_column(JSONB)

    # --- Relationships ---
    authors: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )
    versions: Mapped[list["PaperVersion"]] = relationship(
        "PaperVersion", back_populates="paper", cascade="all, delete-orphan"
    )
    references: Mapped[list["PaperReference"]] = relationship(
        "PaperReference",
        back_populates="citing_paper",
        foreign_keys="PaperReference.citing_paper_id",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["PaperTag"]] = relationship(  # type: ignore[name-defined]
        "PaperTag", cascade="all, delete-orphan",
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

    paper: Mapped["Paper"] = relationship("Paper", back_populates="versions")


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

    citing_paper: Mapped["Paper"] = relationship(
        "Paper", back_populates="references", foreign_keys=[citing_paper_id]
    )
    cited_paper: Mapped["Paper | None"] = relationship(
        "Paper", foreign_keys=[cited_paper_id]
    )

"""Claim & Evidence models — atomic claims, evidence links, argument structure."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    An atomic claim extracted from a paper.

    Represents a single falsifiable statement or contribution claim.
    """

    __tablename__ = "claims"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str | None] = mapped_column(
        String(30)
    )  # contribution, finding, hypothesis, assumption, limitation
    category: Mapped[str | None] = mapped_column(
        String(50)
    )  # architectural, methodological, theoretical, empirical
    hedging_level: Mapped[str | None] = mapped_column(
        String(20)
    )  # strong, moderate, weak — measures language certainty
    confidence: Mapped[float | None] = mapped_column(Float)  # 0-1 extraction confidence
    section_ref: Mapped[str | None] = mapped_column(
        String(100)
    )  # source section: "Introduction", "Results §3.2", etc.
    position: Mapped[int | None] = mapped_column(Integer)  # ordering within paper
    source: Mapped[str | None] = mapped_column(
        String(20), default="llm"
    )  # llm, manual, hybrid
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="claim", cascade="all, delete-orphan"
    )


class EvidenceLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Links a claim to its supporting evidence.

    Evidence can be: a text passage, a figure, a table, or a reference.
    """

    __tablename__ = "evidence_links"

    claim_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # text, figure, table, reference, data
    evidence_text: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(
        String(200)
    )  # "Section 4.2", "Table 3", "Figure 5a"
    strength: Mapped[str | None] = mapped_column(
        String(20)
    )  # strong, moderate, weak, insufficient
    is_sufficient: Mapped[bool | None] = mapped_column(Boolean)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="evidence_links")

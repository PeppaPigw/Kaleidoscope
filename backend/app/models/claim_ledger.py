"""Global Claim Ledger — cross-dossier claim deduplication and conflict detection."""

import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GlobalClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A canonical claim that may appear across multiple dossiers and papers."""

    __tablename__ = "global_claims"

    canonical_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    claim_type: Mapped[str | None] = mapped_column(String(30))
    topic_terms: Mapped[list | None] = mapped_column(JSONB, default=list)
    entities: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    qualifiers: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    first_seen_dossier_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_dossiers.id"), nullable=True
    )
    first_seen_paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True
    )

    support_count: Mapped[int] = mapped_column(Integer, default=0)
    contradict_count: Mapped[int] = mapped_column(Integer, default=0)
    qualify_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    evidence_strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_support: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_contradict: Mapped[float | None] = mapped_column(Float, nullable=True)
    replication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength_breakdown: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    direct_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cascade_depth: Mapped[int] = mapped_column(Integer, default=0)

    mentions: Mapped[list["ClaimMention"]] = relationship(
        "ClaimMention", back_populates="global_claim", cascade="all, delete-orphan"
    )
    outgoing_relations: Mapped[list["ClaimRelation"]] = relationship(
        "ClaimRelation",
        foreign_keys="ClaimRelation.source_claim_id",
        back_populates="source_claim",
        cascade="all, delete-orphan",
    )


class ClaimMention(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A specific occurrence of a global claim in a dossier/paper context."""

    __tablename__ = "claim_mentions"

    global_claim_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("global_claims.id"), nullable=False, index=True
    )
    dossier_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_dossiers.id"), nullable=True, index=True
    )
    paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True, index=True
    )
    source_tool: Mapped[str] = mapped_column(String(50), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    stance: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength_breakdown: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    global_claim: Mapped["GlobalClaim"] = relationship(
        "GlobalClaim", back_populates="mentions"
    )


class ClaimRelation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A directed relationship between two global claims."""

    __tablename__ = "claim_relations"
    __table_args__ = (
        UniqueConstraint("source_claim_id", "target_claim_id", "relation"),
    )

    source_claim_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("global_claims.id"), nullable=False, index=True
    )
    target_claim_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("global_claims.id"), nullable=False, index=True
    )
    relation: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSONB, default=list)
    method: Mapped[str] = mapped_column(String(20), nullable=False)

    source_claim: Mapped["GlobalClaim"] = relationship(
        "GlobalClaim", foreign_keys=[source_claim_id], back_populates="outgoing_relations"
    )
    target_claim: Mapped["GlobalClaim"] = relationship(
        "GlobalClaim", foreign_keys=[target_claim_id]
    )


class ClaimConfidenceEvent(UUIDPrimaryKeyMixin, Base):
    """Log of confidence changes propagated through the dependency graph."""

    __tablename__ = "claim_confidence_events"

    claim_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("global_claims.id"), nullable=False, index=True
    )
    trigger_claim_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("global_claims.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    before_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    after_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[list | None] = mapped_column(JSONB, default=list)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

"""Collaboration models — comments, tasks, and screening (§8).

Provides lightweight collaboration primitives for single-user
and small-team paper review workflows.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class PaperComment(UUIDPrimaryKeyMixin, Base):
    """Threaded comments on papers."""

    __tablename__ = "paper_comments"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_comments.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional: anchor to a specific section/figure
    anchor_type: Mapped[str | None] = mapped_column(String(50))
    anchor_ref: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    replies: Mapped[list["PaperComment"]] = relationship(
        "PaperComment", back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["PaperComment | None"] = relationship(
        "PaperComment", back_populates="replies", remote_side="PaperComment.id"
    )


class ReviewTask(UUIDPrimaryKeyMixin, Base):
    """Assigned review/screening tasks for papers."""

    __tablename__ = "review_tasks"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    assignee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="review"
    )  # review | screen | verify
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )  # pending | in_progress | done | skipped
    priority: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str | None] = mapped_column(String(30))
    decision_metadata: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class ScreeningDecision(UUIDPrimaryKeyMixin, Base):
    """Title/abstract screening decisions for systematic reviews."""

    __tablename__ = "screening_decisions"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    reviewer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # title_abstract | full_text
    decision: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # include | exclude | maybe
    reason: Mapped[str | None] = mapped_column(Text)
    criteria_met: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

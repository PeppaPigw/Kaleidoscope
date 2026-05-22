"""Research Run models — autonomous research execution engine."""

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResearchRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_runs"

    dossier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_dossiers.id"), nullable=False, index=True
    )
    objective: Mapped[str] = mapped_column(String(50), nullable=False, default="maximize_certainty")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running", index=True)
    budget_papers: Mapped[int] = mapped_column(Integer, default=10)
    max_steps: Mapped[int] = mapped_column(Integer, default=20)
    target_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_claims: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    allowed_actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    papers_used: Mapped[int] = mapped_column(Integer, default=0)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    claims_added: Mapped[int] = mapped_column(Integer, default=0)
    claims_updated: Mapped[int] = mapped_column(Integer, default=0)
    contradictions_resolved: Mapped[int] = mapped_column(Integer, default=0)
    net_confidence_delta: Mapped[float] = mapped_column(Float, default=0.0)

    started_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    steps: Mapped[list["ResearchRunStep"]] = relationship(
        "ResearchRunStep", back_populates="run", cascade="all, delete-orphan",
        order_by="ResearchRunStep.step_number",
    )


class ResearchRunStep(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_run_steps"

    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_runs.id"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_claim_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_claim_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    predicted_utility: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_lift: Mapped[float] = mapped_column(Float, default=0.0)
    actual_lift: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    claims_produced: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="steps")

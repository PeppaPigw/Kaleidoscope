"""Decision Monitor models — living decision surveillance."""

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DecisionMonitor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A persistent monitor that watches a compiled decision for trigger events."""

    __tablename__ = "decision_monitors"

    dossier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_dossiers.id"), nullable=False, index=True
    )
    decision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_question: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_option: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    triggers: Mapped[dict | None] = mapped_column(JSONB, default=list)
    assumptions: Mapped[dict | None] = mapped_column(JSONB, default=list)
    boundary_conditions: Mapped[dict | None] = mapped_column(JSONB, default=list)
    decision_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    fragility_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_check_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    recommendation_changed: Mapped[bool] = mapped_column(Boolean, default=False)

    runs: Mapped[list["DecisionMonitorRun"]] = relationship(
        "DecisionMonitorRun", back_populates="monitor", cascade="all, delete-orphan"
    )


class DecisionMonitorRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single execution of a decision monitor check."""

    __tablename__ = "decision_monitor_runs"

    monitor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_monitors.id"), nullable=False, index=True
    )
    started_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggers_checked: Mapped[int] = mapped_column(Integer, default=0)
    triggers_fired: Mapped[int] = mapped_column(Integer, default=0)
    new_evidence_found: Mapped[int] = mapped_column(Integer, default=0)
    drift_delta: Mapped[float] = mapped_column(Float, default=0.0)
    recommendation_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_option: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_option: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    monitor: Mapped["DecisionMonitor"] = relationship("DecisionMonitor", back_populates="runs")

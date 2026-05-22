"""Topic Monitor models — living research surveillance for dossiers."""

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TopicMonitor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A persistent monitor that watches a dossier's topic for new evidence."""

    __tablename__ = "topic_monitors"

    dossier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_dossiers.id"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    query_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    cadence: Mapped[str] = mapped_column(String(20), default="daily")
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_run_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    runs: Mapped[list["TopicMonitorRun"]] = relationship(
        "TopicMonitorRun", back_populates="monitor", cascade="all, delete-orphan"
    )


class TopicMonitorRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single execution of a topic monitor."""

    __tablename__ = "topic_monitor_runs"

    monitor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topic_monitors.id"), nullable=False, index=True
    )
    started_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    papers_checked: Mapped[int] = mapped_column(Integer, default=0)
    papers_new: Mapped[int] = mapped_column(Integer, default=0)
    claims_extracted: Mapped[int] = mapped_column(Integer, default=0)
    ledger_mentions_added: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_found: Mapped[int] = mapped_column(Integer, default=0)
    alerts_emitted: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    monitor: Mapped["TopicMonitor"] = relationship("TopicMonitor", back_populates="runs")

"""Alert & monitoring models — alert rules, notifications, digests."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AlertRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User-defined alert rules that trigger on events."""

    __tablename__ = "alert_rules"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # new_paper, citation_milestone, author_update, keyword_match
    condition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Examples:
    # {"keywords": ["transformer", "attention"], "venue_ids": [...]}
    # {"author_id": "...", "min_citations": 100}
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # ["in_app", "email", "webhook"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)


class Alert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Individual alert notification."""

    __tablename__ = "alerts"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # new_paper, citation, system
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


class Digest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Periodic digest summary."""

    __tablename__ = "digests"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    period: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # daily, weekly
    content: Mapped[str | None] = mapped_column(Text)  # LLM-generated markdown
    paper_ids: Mapped[dict | None] = mapped_column(JSONB)  # [UUID str]
    paper_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

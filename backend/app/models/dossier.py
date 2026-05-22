"""Research Dossier model — persistent research memory for agents."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResearchDossier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A persistent research project that accumulates knowledge across sessions."""

    __tablename__ = "research_dossiers"

    topic: Mapped[str] = mapped_column(Text, nullable=False)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Core state (JSONB for flexibility)
    papers_seen: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    papers_excluded: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    claims: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    evidence: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    gaps: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    decisions: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    open_questions: Mapped[list | None] = mapped_column(JSONB, default=list)
    failed_searches: Mapped[list | None] = mapped_column(JSONB, default=list)
    next_actions: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Computed summaries
    coverage_score: Mapped[int | None] = mapped_column(default=None)
    confidence_summary: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    memory_log: Mapped[list | None] = mapped_column(JSONB, default=list)

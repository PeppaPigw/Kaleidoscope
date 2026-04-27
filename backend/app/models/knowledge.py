"""Personal knowledge models — reading log, annotations, knowledge cards, glossary."""

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ReadingLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks user reading interactions — what was read, when, for how long."""

    __tablename__ = "reading_logs"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # open, read, annotate, search, summarize, ask
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    # e.g. {"sections_viewed": ["intro", "methods"], "scroll_depth": 0.8}


class Annotation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User highlights and notes on papers."""

    __tablename__ = "annotations"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    annotation_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # highlight, note, question, idea
    text: Mapped[str | None] = mapped_column(Text)  # selected/highlighted text
    note: Mapped[str | None] = mapped_column(Text)  # user's note
    color: Mapped[str | None] = mapped_column(String(20))
    page: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[dict | None] = mapped_column(JSONB)  # {start, end, section}


class GlossaryTerm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User or auto-extracted glossary of technical terms."""

    __tablename__ = "glossary_terms"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    term: Mapped[str] = mapped_column(String(200), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(100))  # ML, NLP, CV, etc.
    source_paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True
    )
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    aliases: Mapped[dict | None] = mapped_column(
        JSONB
    )  # ["attention mechanism", "self-attention"]


class KnowledgeCard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Flashcard-style knowledge items for spaced repetition learning."""

    __tablename__ = "knowledge_cards"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    paper_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    card_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="concept"
    )  # concept, formula, method, result
    difficulty: Mapped[str | None] = mapped_column(String(10))  # easy, medium, hard
    # Spaced repetition fields (SM-2)
    review_count: Mapped[int] = mapped_column(Integer, default=0)  # total reviews
    repetition: Mapped[int] = mapped_column(
        Integer, default=0
    )  # successful streak (resets on failure)
    ease_factor: Mapped[float] = mapped_column(default=2.5)  # SM-2 ease factor
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    next_review_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    tags: Mapped[dict | None] = mapped_column(JSONB)  # ["transformer", "attention"]

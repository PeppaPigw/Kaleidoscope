"""Topic model — BERTopic cluster assignments and topic metadata."""


from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Topic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Research topic discovered via BERTopic clustering."""

    __tablename__ = "topics"

    label: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[dict | None] = mapped_column(JSONB)  # [str]
    representative_docs: Mapped[dict | None] = mapped_column(JSONB)  # [UUID str]
    paper_count: Mapped[int] = mapped_column(Integer, default=0)
    trend_direction: Mapped[str | None] = mapped_column(
        String(20)
    )  # rising, stable, declining
    description: Mapped[str | None] = mapped_column(Text)  # LLM-generated
    cluster_id: Mapped[int | None] = mapped_column(Integer)  # BERTopic topic_id

    # Relationships
    papers: Mapped[list["PaperTopic"]] = relationship(
        "PaperTopic", back_populates="topic", cascade="all, delete-orphan"
    )


class PaperTopic(UUIDPrimaryKeyMixin, Base):
    """Many-to-many: paper → topic assignment with probability."""

    __tablename__ = "paper_topics"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True
    )
    probability: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="papers")

"""RSS Feed model — tracks subscribed feeds and their polling state."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RSSFeed(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A subscribed RSS feed source."""

    __tablename__ = "rss_feeds"

    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))  # e.g., "physics", "chemistry"

    # --- Polling State ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    etag: Mapped[str | None] = mapped_column(String(200))  # HTTP ETag for conditional requests
    last_modified: Mapped[str | None] = mapped_column(String(100))  # HTTP Last-Modified header
    poll_error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    # --- Statistics ---
    total_items_discovered: Mapped[int] = mapped_column(Integer, default=0)
    last_item_count: Mapped[int] = mapped_column(Integer, default=0)

    # --- Full-text acquisition capability ---
    pdf_capability: Mapped[str | None] = mapped_column(
        String(20)
    )  # direct, unpaywall, tdm, metadata_only

    # --- Additional config ---
    config: Mapped[dict | None] = mapped_column(JSONB)  # Extra configuration per feed

    def __repr__(self) -> str:
        return f"<RSSFeed(id={self.id}, name={self.name}, url={self.url[:50]}...)>"

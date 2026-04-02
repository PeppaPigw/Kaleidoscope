"""Writing models — persisted user-scoped markdown draft documents."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WritingDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User-owned writing draft stored canonically as Markdown."""

    __tablename__ = "writing_documents"

    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled")
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    plain_text_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cover_image_url: Mapped[str | None] = mapped_column(Text)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

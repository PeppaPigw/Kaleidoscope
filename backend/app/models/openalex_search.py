"""OpenAlexSearch — persisted OpenAlex search results with graph data."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OpenAlexSearch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Stores a single OpenAlex search result set, including similarity-ranked
    papers and the citation-edge graph between them.
    """

    __tablename__ = "openalex_searches"

    query: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    focal_openalex_id: Mapped[str | None] = mapped_column(String(50))
    result_count: Mapped[int] = mapped_column(Integer, default=0)

    # Full result payload (papers + edges)
    results: Mapped[dict | None] = mapped_column(JSONB)
    # {papers: [...], edges: [...], focal_id: "W...", query: "..."}

    def __repr__(self) -> str:
        return f"<OpenAlexSearch(query={self.query[:40]!r}, count={self.result_count})>"

"""Venue model — journals, conferences, and preprint servers."""

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Venue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Journal, conference, or preprint server."""

    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str | None] = mapped_column(
        String(30)
    )  # journal, conference, preprint_server
    issn: Mapped[str | None] = mapped_column(String(20), index=True)
    eissn: Mapped[str | None] = mapped_column(String(20))
    publisher: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(Text)

    # --- Rankings ---
    sjr_quartile: Mapped[str | None] = mapped_column(String(5))  # Q1, Q2, Q3, Q4
    ccf_rank: Mapped[str | None] = mapped_column(String(5))  # A, B, C
    impact_factor: Mapped[float | None] = mapped_column(Float)
    h_index: Mapped[int | None] = mapped_column()

    # --- OpenAlex ---
    openalex_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)

    # --- Relationships ---
    papers: Mapped[list["Paper"]] = relationship("Paper", back_populates="venue")

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name={self.name})>"

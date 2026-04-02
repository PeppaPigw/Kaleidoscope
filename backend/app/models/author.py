"""Author and Institution models."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Author(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Disambiguated author entity. Linked to papers via PaperAuthor."""

    __tablename__ = "authors"

    # --- Identifiers ---
    openalex_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    orcid: Mapped[str | None] = mapped_column(String(30), index=True)
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # --- Profile ---
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases: Mapped[dict | None] = mapped_column(JSONB)  # ["John Doe", "J. Doe"]
    h_index: Mapped[int | None] = mapped_column(Integer)
    paper_count: Mapped[int | None] = mapped_column(Integer)
    citation_count: Mapped[int | None] = mapped_column(Integer)

    # --- Affiliation ---
    institution_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True
    )
    institution: Mapped["Institution | None"] = relationship(
        "Institution", back_populates="members"
    )

    # --- Raw metadata ---
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # --- Relationships ---
    papers: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="author"
    )

    def __repr__(self) -> str:
        return f"<Author(id={self.id}, name={self.display_name})>"


class PaperAuthor(Base):
    """Association table: Paper ↔ Author with ordering and role info."""

    __tablename__ = "paper_authors"

    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), primary_key=True
    )
    author_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("authors.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Author order (0-based)
    is_corresponding: Mapped[bool] = mapped_column(default=False)
    raw_affiliation: Mapped[str | None] = mapped_column(Text)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")
    author: Mapped["Author"] = relationship("Author", back_populates="papers")


class Institution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Research institution / university."""

    __tablename__ = "institutions"

    openalex_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    ror_id: Mapped[str | None] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(5))
    type: Mapped[str | None] = mapped_column(String(50))  # education, company, etc.
    homepage_url: Mapped[str | None] = mapped_column(Text)

    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    members: Mapped[list["Author"]] = relationship(
        "Author", back_populates="institution"
    )

    def __repr__(self) -> str:
        return f"<Institution(id={self.id}, name={self.name})>"

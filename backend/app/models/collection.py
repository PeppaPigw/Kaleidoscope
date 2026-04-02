"""Collection, Tag, and reading status models — P1 organization features.

All workflow state (collections, tags, reading status) is scoped to a
user_id so that multi-user collaboration (P2) does not require a schema
rewrite. Until an auth system is added, user_id defaults to a sentinel
"default" UUID.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Sentinel user ID used before real authentication is added.
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


class ReadingStatus(str, Enum):
    """Paper reading progress."""

    UNREAD = "unread"
    TO_READ = "to_read"
    READING = "reading"
    READ = "read"
    ARCHIVED = "archived"


class UserReadingStatus(Base):
    """
    Per-user, per-paper reading status.

    Separate from the Paper table so that each user can independently
    track their reading progress and the Paper model stays shared.
    """

    __tablename__ = "user_reading_status"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper_reading"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        server_default=DEFAULT_USER_ID,
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="unread")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Collection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    User-created paper collection (folder / reading list).

    Can be a static collection (user manually adds papers)
    or a "smart collection" (defined by a saved filter query
    that dynamically evaluates which papers belong).

    Scoped to user_id for future multi-user support.
    """

    __tablename__ = "collections"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        server_default=DEFAULT_USER_ID,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # "#FF6B35"
    icon: Mapped[str | None] = mapped_column(String(50))  # "folder", "star", etc.

    # Smart collection
    is_smart: Mapped[bool] = mapped_column(default=False)
    smart_filter: Mapped[dict | None] = mapped_column(JSONB)
    # Example filter: {"year_gte": 2023, "keywords": ["transformer"], "has_full_text": true}

    # Denormalized for fast listing
    paper_count: Mapped[int] = mapped_column(Integer, default=0)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    papers: Mapped[list["CollectionPaper"]] = relationship(
        "CollectionPaper",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionPaper.position",
    )

    def __repr__(self) -> str:
        return (
            f"<Collection(id={self.id}, name={self.name}, papers={self.paper_count})>"
        )


class CollectionPaper(Base):
    """
    M2M junction: Paper ↔ Collection.

    Supports ordering (position) and per-paper notes within a collection.
    """

    __tablename__ = "collection_papers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    collection_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False, index=True
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="papers"
    )
    paper: Mapped["Paper"] = relationship("Paper")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<CollectionPaper(collection={self.collection_id}, paper={self.paper_id})>"
        )


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    User-defined tag for paper classification.

    Scoped to user_id for future multi-user support.
    """

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_tag_name"),)

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        server_default=DEFAULT_USER_ID,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))  # "#4ECDC4"
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    papers: Mapped[list["PaperTag"]] = relationship(
        "PaperTag", back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"


class PaperTag(Base):
    """M2M junction: Paper ↔ Tag."""

    __tablename__ = "paper_tags"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True
    )
    tag_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False, index=True
    )
    tagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper")  # noqa: F821
    tag: Mapped["Tag"] = relationship("Tag", back_populates="papers")

    def __repr__(self) -> str:
        return f"<PaperTag(paper={self.paper_id}, tag={self.tag_id})>"

"""Models package — export all ORM models for Alembic and application use."""

from app.models.base import Base
from app.models.paper import Paper, PaperReference, PaperVersion
from app.models.author import Author, Institution, PaperAuthor
from app.models.venue import Venue
from app.models.feed import RSSFeed
from app.models.collection import Collection, CollectionPaper, Tag, PaperTag, UserReadingStatus

__all__ = [
    "Base",
    "Paper",
    "PaperVersion",
    "PaperReference",
    "Author",
    "PaperAuthor",
    "Institution",
    "Venue",
    "RSSFeed",
    "Collection",
    "CollectionPaper",
    "Tag",
    "PaperTag",
    "UserReadingStatus",
]


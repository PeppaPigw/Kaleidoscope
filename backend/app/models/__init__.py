"""Models package — export all ORM models for Alembic and application use."""

from app.models.base import Base
from app.models.paper import Paper, PaperReference, PaperVersion
from app.models.author import Author, Institution, PaperAuthor
from app.models.venue import Venue
from app.models.feed import RSSFeed
from app.models.collection import Collection, CollectionPaper, Tag, PaperTag, UserReadingStatus
from app.models.topic import Topic, PaperTopic
from app.models.alert import AlertRule, Alert, Digest
from app.models.claim import Claim, EvidenceLink
from app.models.knowledge import ReadingLog, Annotation, GlossaryTerm, KnowledgeCard

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
    # P2 models
    "Topic",
    "PaperTopic",
    "AlertRule",
    "Alert",
    "Digest",
    # P3 models
    "Claim",
    "EvidenceLink",
    "ReadingLog",
    "Annotation",
    "GlossaryTerm",
    "KnowledgeCard",
]


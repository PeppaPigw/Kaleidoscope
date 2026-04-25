"""Models package — export all ORM models for Alembic and application use."""

from app.models.alert import Alert, AlertRule, Digest
from app.models.api_key import APIKey
from app.models.author import Author, Institution, PaperAuthor
from app.models.base import Base
from app.models.claim import Claim, EvidenceLink
from app.models.collection import (
    Collection,
    CollectionChatMessage,
    CollectionChatThread,
    CollectionFeedSubscription,
    CollectionPaper,
    PaperTag,
    Tag,
    UserReadingStatus,
)
from app.models.feed import RSSFeed
from app.models.governance import (
    AuditLog,
    ReproductionAttempt,
    SavedSearch,
    UserCorrection,
    Webhook,
)
from app.models.knowledge import Annotation, GlossaryTerm, KnowledgeCard, ReadingLog
from app.models.knowledge_graph import ReadingPathCache
from app.models.paper import MetadataProvenance, Paper, PaperReference, PaperVersion
from app.models.paper_qa import PaperChunk, PaperEmbeddingJob, QAMessage
from app.models.topic import PaperTopic, Topic
from app.models.user import User, UserRole
from app.models.venue import Venue
from app.models.writing import WritingDocument

__all__ = [
    "Base",
    "Paper",
    "PaperVersion",
    "PaperReference",
    "MetadataProvenance",
    "Author",
    "PaperAuthor",
    "Institution",
    "Venue",
    "RSSFeed",
    "Collection",
    "CollectionFeedSubscription",
    "CollectionChatThread",
    "CollectionChatMessage",
    "CollectionPaper",
    "Tag",
    "PaperTag",
    "UserReadingStatus",
    # P2 models
    "Topic",
    "PaperTopic",
    "User",
    "UserRole",
    "WritingDocument",
    "APIKey",
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
    "SavedSearch",
    "AuditLog",
    "Webhook",
    "UserCorrection",
    "ReproductionAttempt",
    "ReadingPathCache",
    "PaperChunk",
    "PaperEmbeddingJob",
    "QAMessage",
]

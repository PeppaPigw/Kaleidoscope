"""RAGFlow dataset/document registry model and service."""

# mypy: disable-error-code="misc"

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import DateTime, ForeignKey, String, Text, func, or_, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RagflowDocumentMapping(Base):
    """Tracks the latest RAGFlow sync state for papers and collection datasets."""

    __tablename__ = "ragflow_document_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id"),
        nullable=True,
        unique=True,
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id"),
        nullable=True,
        unique=True,
    )
    ragflow_dataset_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ragflow_document_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sync_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parse_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class DatasetRegistryService:
    """CRUD helpers for the RAGFlow sync registry table."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _as_uuid(value: str) -> uuid.UUID:
        """Convert string ids into UUID objects for typed comparisons."""
        return uuid.UUID(value)

    async def get_by_paper_id(self, paper_id: str) -> RagflowDocumentMapping | None:
        """Return the mapping row for a paper, if present."""
        result = await self.db.execute(
            select(RagflowDocumentMapping).where(
                RagflowDocumentMapping.paper_id == self._as_uuid(paper_id)
            )
        )
        return cast(RagflowDocumentMapping | None, result.scalar_one_or_none())

    async def get_by_collection_id(
        self,
        collection_id: str,
    ) -> RagflowDocumentMapping | None:
        """Return the mapping row for a collection dataset, if present."""
        result = await self.db.execute(
            select(RagflowDocumentMapping).where(
                RagflowDocumentMapping.collection_id == self._as_uuid(collection_id)
            )
        )
        return cast(RagflowDocumentMapping | None, result.scalar_one_or_none())

    async def get_by_id(self, mapping_id: str) -> RagflowDocumentMapping | None:
        """Return a mapping row by its primary key."""
        result = await self.db.execute(
            select(RagflowDocumentMapping).where(
                RagflowDocumentMapping.id == self._as_uuid(mapping_id)
            )
        )
        return cast(RagflowDocumentMapping | None, result.scalar_one_or_none())

    async def upsert(
        self,
        paper_id: str | None,
        collection_id: str | None,
        dataset_id: str,
        document_id: str | None,
        sync_hash: str | None,
        parse_status: str,
    ) -> RagflowDocumentMapping:
        """Insert or update a paper/collection mapping row."""
        mapping: RagflowDocumentMapping | None = None
        if paper_id is not None:
            mapping = await self.get_by_paper_id(paper_id)
        if mapping is None and collection_id is not None:
            mapping = await self.get_by_collection_id(collection_id)

        now = datetime.now(UTC)
        if mapping is None:
            mapping = RagflowDocumentMapping(
                paper_id=paper_id,
                collection_id=collection_id,
                ragflow_dataset_id=dataset_id,
                ragflow_document_id=document_id,
                sync_hash=sync_hash,
                parse_status=parse_status,
                synced_at=now,
                error_message=None,
            )
            self.db.add(mapping)
        else:
            mapping.paper_id = uuid.UUID(paper_id) if paper_id is not None else None
            mapping.collection_id = (
                uuid.UUID(collection_id) if collection_id is not None else None
            )
            mapping.ragflow_dataset_id = dataset_id
            mapping.ragflow_document_id = document_id
            mapping.sync_hash = sync_hash
            mapping.parse_status = parse_status
            mapping.synced_at = now
            mapping.error_message = None

        await self.db.flush()
        return mapping

    async def mark_failed(self, mapping_id: str, error_message: str) -> None:
        """Mark a mapping as failed and persist the latest error message."""
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return
        mapping.parse_status = "failed"
        mapping.error_message = error_message[:1000]
        mapping.synced_at = datetime.now(UTC)
        await self.db.flush()

    async def update_status(
        self,
        mapping_id: str,
        parse_status: str,
        *,
        error_message: str | None = None,
    ) -> RagflowDocumentMapping | None:
        """Update parse status and optionally clear or replace the latest error."""
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return None
        mapping.parse_status = parse_status
        mapping.error_message = error_message[:1000] if error_message else None
        mapping.synced_at = datetime.now(UTC)
        await self.db.flush()
        return mapping

    async def delete_by_paper_id(self, paper_id: str) -> bool:
        """Delete the mapping row for a paper, if present."""
        mapping = await self.get_by_paper_id(paper_id)
        if mapping is None:
            return False
        await self.db.delete(mapping)
        await self.db.flush()
        return True

    async def delete_by_collection_id(self, collection_id: str) -> bool:
        """Delete the mapping row for a collection dataset, if present."""
        mapping = await self.get_by_collection_id(collection_id)
        if mapping is None:
            return False
        await self.db.delete(mapping)
        await self.db.flush()
        return True

    async def list_stale(self, freshness_minutes: int) -> list[RagflowDocumentMapping]:
        """Return mappings that are unsynced, aging out, or not yet done."""
        cutoff = datetime.now(UTC) - timedelta(minutes=freshness_minutes)
        result = await self.db.execute(
            select(RagflowDocumentMapping).where(
                or_(
                    RagflowDocumentMapping.synced_at.is_(None),
                    RagflowDocumentMapping.synced_at < cutoff,
                    RagflowDocumentMapping.parse_status.in_(
                        ["pending", "processing", "failed"]
                    ),
                )
            )
        )
        return list(result.scalars().all())

    async def list_processing(self) -> list[RagflowDocumentMapping]:
        """Return all mappings with 'processing' parse status."""
        result = await self.db.execute(
            select(RagflowDocumentMapping).where(
                RagflowDocumentMapping.parse_status == "processing"
            )
        )
        return list(result.scalars().all())

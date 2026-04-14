"""Services that sync Kaleidoscope paper content into RAGFlow."""

from __future__ import annotations

import hashlib
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.author import PaperAuthor
from app.models.collection import Collection, CollectionPaper
from app.models.paper import Paper
from app.models.topic import PaperTopic
from app.services.extraction.chunker import TextChunker
from app.services.quality_service import QualityService
from app.services.ragflow.dataset_registry import (
    DatasetRegistryService,
    RagflowDocumentMapping,
)
from app.services.ragflow.ragflow_client import RagflowClient

logger = structlog.get_logger(__name__)


class DocumentSyncService:
    """Pushes normalized paper markdown and metadata into RAGFlow."""

    def __init__(
        self,
        db: AsyncSession,
        ragflow_client: RagflowClient | None = None,
        registry: DatasetRegistryService | None = None,
    ):
        self.db = db
        self.ragflow_client = ragflow_client or RagflowClient()
        self.registry = registry or DatasetRegistryService(db)

    async def sync_paper(self, paper_id: str) -> dict[str, Any]:
        """Sync a single paper into its configured RAGFlow dataset."""
        if not settings.ragflow_sync_enabled:
            return {"enabled": False, "status": "disabled", "paper_id": paper_id}

        log = logger.bind(paper_id=paper_id)
        paper = await self._get_paper(paper_id)
        if paper is None:
            return {"enabled": True, "status": "not_found", "paper_id": paper_id}

        content = TextChunker.prepare_paper_text(paper).strip()
        if not content:
            # Clean up any stale mapping/document if content has been removed
            await self._cleanup_stale_paper(paper_id, log)
            return {"enabled": True, "status": "no_content", "paper_id": paper_id}

        sync_hash = self._compute_hash(content)
        mapping = await self.registry.get_by_paper_id(paper_id)
        if mapping is not None and mapping.sync_hash == sync_hash:
            if mapping.parse_status == "done" and mapping.ragflow_document_id:
                log.info("ragflow_sync_paper_skipped", reason="unchanged")
                return {
                    "enabled": True,
                    "status": "skipped",
                    "paper_id": paper_id,
                    "dataset_id": mapping.ragflow_dataset_id,
                    "document_id": mapping.ragflow_document_id,
                }
            # Same hash but still processing — poll instead of re-uploading
            if mapping.parse_status == "processing" and mapping.ragflow_document_id:
                return await self._poll_and_update(
                    mapping,
                    paper_id,
                    log,
                    entity_type="paper",
                )

        try:
            dataset_id = await self._resolve_paper_dataset_id(paper_id, mapping)
            metadata = await self.get_paper_metadata(paper)
            metadata["sync_hash"] = sync_hash

            if (
                mapping is not None
                and mapping.ragflow_document_id
                and mapping.ragflow_dataset_id == dataset_id
                and mapping.sync_hash != sync_hash
            ):
                try:
                    await self.ragflow_client.delete_document(
                        dataset_id,
                        mapping.ragflow_document_id,
                    )
                except Exception as exc:  # noqa: BLE001
                    log.warning(
                        "ragflow_delete_previous_document_failed", error=str(exc)
                    )

            upload = await self.ragflow_client.upload_document(
                dataset_id=dataset_id,
                filename=f"{paper_id}.md",
                content_bytes=content.encode("utf-8"),
                metadata=metadata,
            )
            document_id = self._document_id(upload)
            parse_status = "processing"
            if document_id is not None:
                try:
                    status_payload = await self.ragflow_client.get_document_status(
                        dataset_id=dataset_id,
                        document_id=document_id,
                    )
                    parse_status = self._normalize_status(status_payload)
                except Exception as exc:  # noqa: BLE001
                    log.warning("ragflow_document_status_failed", error=str(exc))

            saved = await self.registry.upsert(
                paper_id=paper_id,
                collection_id=None,
                dataset_id=dataset_id,
                document_id=document_id,
                sync_hash=sync_hash,
                parse_status=parse_status,
            )
            if parse_status == "failed":
                await self.registry.mark_failed(
                    str(saved.id), "RAGFlow reported failure"
                )

            log.info(
                "ragflow_sync_paper_complete",
                dataset_id=dataset_id,
                document_id=document_id,
                parse_status=parse_status,
            )
            return {
                "enabled": True,
                "status": parse_status,
                "paper_id": paper_id,
                "dataset_id": dataset_id,
                "document_id": document_id,
            }
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            log.error("ragflow_sync_paper_failed", error=error_message)
            if mapping is not None:
                await self.registry.mark_failed(str(mapping.id), error_message)
            return {
                "enabled": True,
                "status": "error",
                "paper_id": paper_id,
                "error": error_message,
            }

    async def sync_collection(self, collection_id: str) -> dict[str, Any]:
        """Sync every paper in a collection into a dedicated collection dataset."""
        if not settings.ragflow_sync_enabled:
            return {
                "enabled": False,
                "status": "disabled",
                "collection_id": collection_id,
            }

        log = logger.bind(collection_id=collection_id)
        collection = await self._get_collection(collection_id)
        if collection is None:
            return {
                "enabled": True,
                "status": "not_found",
                "collection_id": collection_id,
            }

        papers = await self._get_collection_papers(collection_id)
        paper_hashes: list[str] = []
        prepared: list[tuple[Paper, str, str, dict[str, Any]]] = []
        for paper in papers:
            content = TextChunker.prepare_paper_text(paper).strip()
            if not content:
                continue
            sync_hash = self._compute_hash(content)
            metadata = await self.get_paper_metadata(paper)
            metadata["sync_hash"] = sync_hash
            metadata["collection_id"] = collection_id
            paper_hashes.append(f"{paper.id}:{sync_hash}")
            prepared.append((paper, content, sync_hash, metadata))

        if not prepared:
            # Clean up stale dataset if all content removed
            await self._cleanup_stale_collection(collection_id, log)
            return {
                "enabled": True,
                "status": "no_content",
                "collection_id": collection_id,
                "synced": 0,
            }

        collection_hash = self._compute_hash("\n".join(sorted(paper_hashes)))
        mapping = await self.registry.get_by_collection_id(collection_id)
        if (
            mapping is not None
            and mapping.sync_hash == collection_hash
            and mapping.parse_status == "done"
        ):
            log.info("ragflow_sync_collection_skipped", reason="unchanged")
            return {
                "enabled": True,
                "status": "skipped",
                "collection_id": collection_id,
                "dataset_id": mapping.ragflow_dataset_id,
                "synced": len(prepared),
            }

        try:
            dataset_id = await self._resolve_collection_dataset_id(
                collection,
                collection_hash,
                mapping,
            )
            synced = 0
            errors: list[str] = []
            for paper, content, _, metadata in prepared:
                try:
                    await self.ragflow_client.upload_document(
                        dataset_id=dataset_id,
                        filename=f"{collection_id}-{paper.id}.md",
                        content_bytes=content.encode("utf-8"),
                        metadata=metadata,
                    )
                    synced += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{paper.id}: {exc}")
                    log.error(
                        "ragflow_sync_collection_paper_failed",
                        paper_id=str(paper.id),
                        error=str(exc),
                    )

            parse_status = "processing" if not errors else "failed"
            saved = await self.registry.upsert(
                paper_id=None,
                collection_id=collection_id,
                dataset_id=dataset_id,
                document_id=None,
                sync_hash=collection_hash,
                parse_status=parse_status,
            )
            if errors:
                await self.registry.mark_failed(str(saved.id), "; ".join(errors))

            return {
                "enabled": True,
                "status": parse_status,
                "collection_id": collection_id,
                "dataset_id": dataset_id,
                "synced": synced,
                "failed": len(errors),
                "errors": errors,
            }
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            log.error("ragflow_sync_collection_failed", error=error_message)
            if mapping is not None:
                await self.registry.mark_failed(str(mapping.id), error_message)
            return {
                "enabled": True,
                "status": "error",
                "collection_id": collection_id,
                "error": error_message,
            }

    async def get_paper_metadata(self, paper: Paper) -> dict[str, Any]:
        """Build the RAGFlow document metadata payload for a paper."""
        collection_ids = await self._collection_ids_for_paper(str(paper.id))
        topic_ids = await self._topic_ids_for_paper(str(paper.id))
        quality_svc = QualityService(self.db)
        quality_result = await quality_svc.score_metadata(str(paper.id))
        authors = self._author_names(paper)
        year = paper.published_at.year if paper.published_at is not None else None
        venue = paper.venue.name if paper.venue is not None else None
        if venue is None:
            raw_metadata = paper.raw_metadata or {}
            venue = raw_metadata.get("venue") or raw_metadata.get("container-title")

        return {
            "paper_id": str(paper.id),
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": "|".join(authors),
            "year": year,
            "venue": venue,
            "topic_ids": ",".join(topic_ids),
            "collection_ids": ",".join(collection_ids),
            "parser_name": paper.parser_version or "unknown",
            "quality_score": quality_result.get("score_pct"),
            "retraction_status": self._retraction_status(paper),
            "language": paper.language,
            "published_at": (
                paper.published_at.isoformat()
                if paper.published_at is not None
                else None
            ),
            "paper_type": paper.paper_type,
            "source_type": paper.source_type,
            "sync_hash": "",
        }

    async def _poll_and_update(
        self,
        mapping: RagflowDocumentMapping,
        entity_id: str,
        log: Any,
        *,
        entity_type: str = "paper",
    ) -> dict[str, Any]:
        """Poll RAGFlow for current parse status and update the mapping."""
        try:
            status_payload = await self.ragflow_client.get_document_status(
                dataset_id=str(mapping.ragflow_dataset_id),
                document_id=str(mapping.ragflow_document_id),
            )
            new_status = self._normalize_status(status_payload)
        except Exception as exc:  # noqa: BLE001
            log.warning("ragflow_poll_status_failed", error=str(exc))
            new_status = "processing"

        if new_status != mapping.parse_status:
            await self.registry.update_status(str(mapping.id), new_status)
            log.info(
                f"ragflow_poll_{entity_type}_status_updated",
                old_status=mapping.parse_status,
                new_status=new_status,
            )

        return {
            "enabled": True,
            "status": new_status,
            f"{entity_type}_id": entity_id,
            "dataset_id": str(mapping.ragflow_dataset_id),
            "document_id": str(mapping.ragflow_document_id),
        }

    async def _cleanup_stale_paper(self, paper_id: str, log: Any) -> None:
        """Delete any existing RAGFlow document and mapping when paper content is gone."""
        mapping = await self.registry.get_by_paper_id(paper_id)
        if mapping is None:
            return
        if mapping.ragflow_document_id and mapping.ragflow_dataset_id:
            try:
                await self.ragflow_client.delete_document(
                    mapping.ragflow_dataset_id,
                    mapping.ragflow_document_id,
                )
                if log is not None:
                    log.info(
                        "ragflow_stale_paper_document_deleted",
                        dataset_id=mapping.ragflow_dataset_id,
                        document_id=mapping.ragflow_document_id,
                    )
            except Exception as exc:  # noqa: BLE001
                if log is not None:
                    log.warning("ragflow_stale_paper_delete_failed", error=str(exc))
        await self.registry.delete_by_paper_id(paper_id)

    async def _cleanup_stale_collection(self, collection_id: str, log: Any) -> None:
        """Delete mapping when all collection content has been removed."""
        mapping = await self.registry.get_by_collection_id(collection_id)
        if mapping is None:
            return
        log.info(
            "ragflow_stale_collection_mapping_deleted",
            dataset_id=mapping.ragflow_dataset_id,
        )
        await self.registry.delete_by_collection_id(collection_id)

    async def _get_paper(self, paper_id: str) -> Paper | None:
        """Fetch a paper with the relationships needed for metadata generation."""
        result = await self.db.execute(
            select(Paper)
            .where(Paper.id == paper_id, Paper.deleted_at.is_(None))
            .options(
                selectinload(Paper.authors).selectinload(PaperAuthor.author),
                selectinload(Paper.venue),
            )
        )
        return result.scalar_one_or_none()

    async def _get_collection(self, collection_id: str) -> Collection | None:
        """Fetch a collection record if it exists."""
        result = await self.db.execute(
            select(Collection).where(
                Collection.id == collection_id,
                Collection.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _get_collection_papers(self, collection_id: str) -> list[Paper]:
        """Fetch all active papers currently assigned to a collection."""
        result = await self.db.execute(
            select(Paper)
            .join(CollectionPaper, CollectionPaper.paper_id == Paper.id)
            .where(
                CollectionPaper.collection_id == collection_id,
                Paper.deleted_at.is_(None),
            )
            .options(
                selectinload(Paper.authors).selectinload(PaperAuthor.author),
                selectinload(Paper.venue),
            )
        )
        return list(result.scalars().all())

    async def _resolve_paper_dataset_id(
        self,
        paper_id: str,
        mapping: RagflowDocumentMapping | None,
    ) -> str:
        """Pick the dataset that should receive paper-level document syncs."""
        if mapping is not None and mapping.ragflow_dataset_id:
            return str(mapping.ragflow_dataset_id)
        if settings.ragflow_dataset_papers:
            return str(settings.ragflow_dataset_papers)
        dataset = await self.ragflow_client.create_dataset(
            name=f"paper-{paper_id}",
            embedding_model=settings.embed_model,
            chunk_method="markdown",
        )
        dataset_id = dataset.get("id") or dataset.get("dataset_id")
        if not dataset_id:
            raise ValueError("RAGFlow dataset creation returned no dataset id")
        return str(dataset_id)

    async def _resolve_collection_dataset_id(
        self,
        collection: Collection,
        collection_hash: str,
        mapping: RagflowDocumentMapping | None = None,
    ) -> str:
        """Reuse existing dataset or create a fresh one for collection sync."""
        if mapping is not None and mapping.ragflow_dataset_id:
            return str(mapping.ragflow_dataset_id)
        dataset = await self.ragflow_client.create_dataset(
            name=f"collection-{collection.id}-{collection_hash[:8]}",
            embedding_model=settings.embed_model,
            chunk_method="markdown",
        )
        dataset_id = dataset.get("id") or dataset.get("dataset_id")
        if not dataset_id:
            raise ValueError("RAGFlow dataset creation returned no dataset id")
        return str(dataset_id)

    async def _collection_ids_for_paper(self, paper_id: str) -> list[str]:
        """Return all collection ids currently containing the paper."""
        result = await self.db.execute(
            select(CollectionPaper.collection_id).where(
                CollectionPaper.paper_id == paper_id
            )
        )
        return [str(value) for value in result.scalars().all()]

    async def _topic_ids_for_paper(self, paper_id: str) -> list[str]:
        """Return all topic ids assigned to the paper."""
        result = await self.db.execute(
            select(PaperTopic.topic_id).where(PaperTopic.paper_id == paper_id)
        )
        return [str(value) for value in result.scalars().all()]

    @staticmethod
    def _author_names(paper: Paper) -> list[str]:
        """Return author names in paper order."""
        names = [
            association.author.display_name
            for association in sorted(paper.authors, key=lambda item: item.position)
            if association.author is not None
        ]
        if names:
            return names
        raw_metadata = paper.raw_metadata or {}
        raw_authors = (
            raw_metadata.get("authors_parsed") or raw_metadata.get("authors") or []
        )
        return [str(author) for author in raw_authors if author]

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute a stable SHA-256 hash for synced content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _document_id(payload: dict[str, Any]) -> str | None:
        """Extract a document id from the upload response payload."""
        for key in ("id", "document_id", "doc_id"):
            value = payload.get(key)
            if value:
                return str(value)
        return None

    @staticmethod
    def _normalize_status(payload: dict[str, Any]) -> str:
        """Map RAGFlow status strings into registry-friendly values."""
        for key in ("status", "parse_status", "state"):
            value = payload.get(key)
            if not value:
                continue
            normalized = str(value).lower()
            if normalized in {"pending", "processing", "done", "failed"}:
                return normalized
            if normalized in {"queued", "running"}:
                return "processing"
            if normalized in {"complete", "completed", "success"}:
                return "done"
            if normalized in {"error"}:
                return "failed"
        return "processing"

    @staticmethod
    def _retraction_status(paper: Paper) -> str:
        """Infer the most useful retraction status for RAGFlow metadata."""
        raw_metadata = paper.raw_metadata or {}
        raw_retraction = raw_metadata.get("retraction")
        if isinstance(raw_retraction, str) and raw_retraction.strip():
            return raw_retraction.strip()
        if isinstance(raw_retraction, dict):
            for key in ("status", "label", "source"):
                value = raw_retraction.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if paper.ingestion_status == "retracted":
            return "retracted"
        return "unknown"

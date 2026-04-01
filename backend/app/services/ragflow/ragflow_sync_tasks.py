"""Celery tasks for RAGFlow sync and reconciliation."""
# mypy: disable-error-code="untyped-decorator"

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import settings
from app.dependencies import async_session_factory
from app.services.ragflow.dataset_registry import DatasetRegistryService
from app.services.ragflow.document_sync_service import DocumentSyncService
from app.worker import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="ragflow.sync_paper", queue="ragflow")
def sync_paper_task(paper_id: str) -> dict[str, Any]:
    """Queue-safe wrapper for syncing a single paper into RAGFlow."""

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as session:
            service = DocumentSyncService(session)
            result = await service.sync_paper(paper_id)
            await session.commit()
            return result

    return asyncio.run(_run())


@celery_app.task(name="ragflow.sync_collection", queue="ragflow")
def sync_collection_task(collection_id: str) -> dict[str, Any]:
    """Queue-safe wrapper for syncing a collection dataset into RAGFlow."""

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as session:
            service = DocumentSyncService(session)
            result = await service.sync_collection(collection_id)
            await session.commit()
            return result

    return asyncio.run(_run())


@celery_app.task(name="ragflow.reconcile", queue="ragflow")
def reconcile_sync_task() -> dict[str, Any]:
    """Find stale mappings and re-queue sync work."""

    async def _run() -> dict[str, Any]:
        if not settings.ragflow_sync_enabled:
            return {"skipped": True}
        async with async_session_factory() as session:
            registry = DatasetRegistryService(session)
            stale = await registry.list_stale(settings.ragflow_sync_freshness_minutes)
            queued_papers = 0
            queued_collections = 0
            for mapping in stale:
                if mapping.paper_id is not None:
                    sync_paper_task.delay(str(mapping.paper_id))
                    queued_papers += 1
                elif mapping.collection_id is not None:
                    sync_collection_task.delay(str(mapping.collection_id))
                    queued_collections += 1
            logger.info(
                "ragflow_reconcile_complete",
                queued_papers=queued_papers,
                queued_collections=queued_collections,
            )
            return {
                "queued_papers": queued_papers,
                "queued_collections": queued_collections,
                "stale_mappings": len(stale),
            }

    return asyncio.run(_run())


@celery_app.task(name="ragflow.poll_parse_status", queue="ragflow")
def poll_parse_status_task() -> dict[str, Any]:
    """Poll RAGFlow for processing mappings and promote to done/failed."""

    async def _run() -> dict[str, Any]:
        if not settings.ragflow_sync_enabled:
            return {"skipped": True}
        async with async_session_factory() as session:
            service = DocumentSyncService(session)
            registry = DatasetRegistryService(session)
            processing = await registry.list_processing()
            promoted = 0
            failed = 0
            for mapping in processing:
                entity_id = str(mapping.paper_id or mapping.collection_id)
                entity_type = "paper" if mapping.paper_id else "collection"
                result = await service._poll_and_update(
                    mapping, entity_id, logger, entity_type=entity_type,
                )
                status = result.get("status", "processing")
                if status == "done":
                    promoted += 1
                elif status == "failed":
                    failed += 1
            await session.commit()
            return {
                "checked": len(processing),
                "promoted": promoted,
                "failed": failed,
            }

    return asyncio.run(_run())

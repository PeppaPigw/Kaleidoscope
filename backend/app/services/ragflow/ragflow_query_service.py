"""Workspace and paper query helpers backed by RAGFlow."""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.ragflow.dataset_registry import DatasetRegistryService
from app.services.ragflow.ragflow_client import RagflowClient

logger = structlog.get_logger(__name__)


class RagflowQueryService:
    """Routes workspace and paper Q&A through the RAGFlow sidecar."""

    def __init__(
        self,
        db: AsyncSession,
        ragflow_client: RagflowClient | None = None,
        registry: DatasetRegistryService | None = None,
    ):
        self.db = db
        self.ragflow_client = ragflow_client or RagflowClient()
        self.registry = registry or DatasetRegistryService(db)

    async def ask_workspace(
        self,
        collection_id: str,
        question: str,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """Ask a grounded question against a synced workspace dataset."""
        if not settings.ragflow_sync_enabled:
            return {"enabled": False, "answer": None, "sources": []}

        mapping = await self.registry.get_by_collection_id(collection_id)
        if mapping is None:
            return {"enabled": True, "answer": None, "sources": [], "latency_ms": 0}
        if mapping.parse_status != "done":
            return self._query_not_ready_response()

        started = time.perf_counter()
        try:
            response = await self.ragflow_client.chat_completion(
                dataset_ids=[mapping.ragflow_dataset_id],
                messages=[{"role": "user", "content": question}],
                top_k=top_k,
                filters=None,
            )
        except httpx.HTTPError as exc:
            latency_ms = self._latency_ms(started)
            logger.warning(
                "ragflow_workspace_query_http_error",
                collection_id=collection_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_answer_response(latency_ms)
        except Exception as exc:  # noqa: BLE001
            latency_ms = self._latency_ms(started)
            logger.error(
                "ragflow_workspace_query_failed",
                collection_id=collection_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_answer_response(latency_ms)
        latency_ms = self._latency_ms(started)
        return {
            "enabled": True,
            "answer": self._extract_answer(response),
            "sources": self._extract_sources(response),
            "latency_ms": latency_ms,
        }

    async def ask_paper(
        self,
        paper_id: str,
        question: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Ask a grounded question against a single paper's synced scope."""
        if not settings.ragflow_sync_enabled:
            return {"enabled": False, "answer": None, "sources": []}

        mapping = await self.registry.get_by_paper_id(paper_id)
        if mapping is None:
            return {"enabled": True, "answer": None, "sources": [], "latency_ms": 0}
        if mapping.parse_status != "done":
            return self._query_not_ready_response()

        started = time.perf_counter()
        try:
            response = await self.ragflow_client.chat_completion(
                dataset_ids=[mapping.ragflow_dataset_id],
                messages=[{"role": "user", "content": question}],
                top_k=top_k,
                filters={"paper_id": paper_id},
            )
        except httpx.HTTPError as exc:
            latency_ms = self._latency_ms(started)
            logger.warning(
                "ragflow_paper_query_http_error",
                paper_id=paper_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_answer_response(latency_ms)
        except Exception as exc:  # noqa: BLE001
            latency_ms = self._latency_ms(started)
            logger.error(
                "ragflow_paper_query_failed",
                paper_id=paper_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_answer_response(latency_ms)
        latency_ms = self._latency_ms(started)
        return {
            "enabled": True,
            "answer": self._extract_answer(response),
            "sources": self._extract_sources(response),
            "latency_ms": latency_ms,
        }

    async def get_evidence_pack(
        self,
        collection_id: str,
        question: str,
        top_k: int = 15,
    ) -> dict[str, Any]:
        """Return raw retrieval chunks and metadata for a workspace question."""
        if not settings.ragflow_sync_enabled:
            return {"enabled": False, "chunks": [], "total": 0}

        mapping = await self.registry.get_by_collection_id(collection_id)
        if mapping is None:
            return {"enabled": True, "chunks": [], "total": 0}
        if mapping.parse_status != "done":
            return self._evidence_not_ready_response()

        started = time.perf_counter()
        try:
            chunks = await self.ragflow_client.retrieve(
                dataset_ids=[mapping.ragflow_dataset_id],
                query=question,
                top_k=top_k,
                filters=None,
            )
        except httpx.HTTPError as exc:
            latency_ms = self._latency_ms(started)
            logger.warning(
                "ragflow_workspace_evidence_http_error",
                collection_id=collection_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_evidence_response(latency_ms)
        except Exception as exc:  # noqa: BLE001
            latency_ms = self._latency_ms(started)
            logger.error(
                "ragflow_workspace_evidence_failed",
                collection_id=collection_id,
                dataset_id=mapping.ragflow_dataset_id,
                error=str(exc),
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
            )
            return self._degraded_evidence_response(latency_ms)
        normalized_chunks = [self._normalize_chunk(chunk) for chunk in chunks]
        return {
            "enabled": True,
            "chunks": normalized_chunks,
            "total": len(normalized_chunks),
        }

    async def scoped_retrieve(
        self,
        question: str,
        *,
        dataset_ids: list[str] | None = None,
        collection_id: str | None = None,
        topic: str | None = None,
        venue: str | None = None,
        year: int | None = None,
        author: str | None = None,
        parser_quality: str | None = None,
        top_k: int = 15,
    ) -> dict[str, Any]:
        """Metadata-filtered retrieval — scope by any combination of facets."""
        if not settings.ragflow_sync_enabled:
            return {"enabled": False, "chunks": [], "total": 0}

        # Resolve dataset IDs
        resolved_ids: list[str] = list(dataset_ids or [])
        if collection_id and not resolved_ids:
            mapping = await self.registry.get_by_collection_id(collection_id)
            if mapping and mapping.parse_status == "done":
                resolved_ids.append(str(mapping.ragflow_dataset_id))
        if not resolved_ids:
            return {"enabled": True, "chunks": [], "total": 0}

        # Build metadata filter dict
        filters: dict[str, Any] = {}
        if topic:
            filters["topic"] = topic
        if venue:
            filters["venue"] = venue
        if year:
            filters["year"] = year
        if author:
            filters["author"] = author
        if parser_quality:
            filters["parser_quality"] = parser_quality

        started = time.perf_counter()
        try:
            chunks = await self.ragflow_client.retrieve(
                dataset_ids=resolved_ids,
                query=question,
                top_k=top_k,
                filters=filters or None,
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = self._latency_ms(started)
            logger.warning(
                "scoped_retrieve_failed",
                error=str(exc),
                latency_ms=latency_ms,
            )
            return self._degraded_evidence_response(latency_ms)

        normalized = [self._normalize_chunk(c) for c in chunks]
        latency_ms = self._latency_ms(started)
        return {
            "enabled": True,
            "chunks": normalized,
            "total": len(normalized),
            "filters_applied": filters,
            "latency_ms": latency_ms,
        }

    @staticmethod
    def _latency_ms(started: float) -> int:
        """Return elapsed wall-clock time in milliseconds."""
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _query_not_ready_response() -> dict[str, Any]:
        """Return the standard query payload while a sync is still parsing."""
        return {
            "enabled": True,
            "ready": False,
            "answer": None,
            "sources": [],
            "message": "sync_in_progress",
        }

    @staticmethod
    def _evidence_not_ready_response() -> dict[str, Any]:
        """Return the standard evidence payload while a sync is still parsing."""
        return {
            "enabled": True,
            "ready": False,
            "chunks": [],
            "total": 0,
            "message": "sync_in_progress",
        }

    @staticmethod
    def _degraded_answer_response(latency_ms: int) -> dict[str, Any]:
        """Return a graceful fallback when the RAGFlow sidecar is unavailable."""
        return {
            "enabled": True,
            "answer": None,
            "sources": [],
            "error": "ragflow_unavailable",
            "latency_ms": latency_ms,
        }

    @staticmethod
    def _degraded_evidence_response(latency_ms: int) -> dict[str, Any]:
        """Return a graceful fallback evidence payload when RAGFlow is unavailable."""
        return {
            "enabled": True,
            "chunks": [],
            "total": 0,
            "error": "ragflow_unavailable",
            "latency_ms": latency_ms,
        }

    @staticmethod
    def _extract_answer(response: dict[str, Any]) -> str | None:
        """Extract the answer text from a RAGFlow chat completion payload."""
        if "answer" in response:
            answer = response.get("answer")
            return str(answer) if answer is not None else None
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content")
                    if content is not None:
                        return str(content)
        message = response.get("message")
        return str(message) if message is not None else None

    @staticmethod
    def _extract_sources(response: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract source/citation blocks from a chat completion payload."""
        for key in ("sources", "citations", "references"):
            value = response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                metadata = first.get("metadata")
                if isinstance(metadata, dict):
                    for key in ("sources", "citations", "references"):
                        value = metadata.get(key)
                        if isinstance(value, list):
                            return [item for item in value if isinstance(item, dict)]
        return []

    @staticmethod
    def _normalize_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
        """Normalize retrieval chunk payloads into a stable response shape."""
        metadata = chunk.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        content = (
            chunk.get("content")
            or chunk.get("text")
            or chunk.get("chunk")
            or chunk.get("body")
        )
        return {
            "content": content,
            "score": chunk.get("score"),
            "metadata": metadata,
            "paper_metadata": metadata,
        }

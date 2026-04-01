"""Async client for the Phase 5a RAGFlow sidecar API."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import Any

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

RETRYABLE_STATUS_CODES = {429, 502, 503}


class RagflowClient:
    """Thin async wrapper around the RAGFlow REST API."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_url = (api_url or settings.ragflow_api_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.ragflow_api_key
        self.transport = transport
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Create or reuse the underlying httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                transport=self.transport,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client if it was created."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def create_dataset(
        self,
        name: str,
        embedding_model: str,
        chunk_method: str,
    ) -> dict[str, Any]:
        """Create a new dataset in RAGFlow."""
        payload = await self._request(
            "POST",
            "/api/v1/datasets",
            json={
                "name": name,
                "embedding_model": embedding_model,
                "chunk_method": chunk_method,
            },
        )
        data = self._unwrap(payload)
        return data if isinstance(data, dict) else {}

    async def list_datasets(self) -> list[dict[str, Any]]:
        """List available datasets."""
        payload = await self._request("GET", "/api/v1/datasets")
        data = self._unwrap(payload)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("items", "datasets", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    async def upload_document(
        self,
        dataset_id: str,
        filename: str,
        content_bytes: bytes,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Upload a markdown document into a dataset."""
        payload = await self._request(
            "POST",
            f"/api/v1/datasets/{dataset_id}/documents",
            files={"file": (filename, content_bytes, "text/markdown")},
            data={"metadata": json.dumps(metadata)},
        )
        data = self._unwrap(payload)
        return data if isinstance(data, dict) else {}

    async def get_document_status(
        self,
        dataset_id: str,
        document_id: str,
    ) -> dict[str, Any]:
        """Fetch the latest status for a RAGFlow document."""
        payload = await self._request(
            "GET",
            f"/api/v1/datasets/{dataset_id}/documents/{document_id}",
        )
        data = self._unwrap(payload)
        return data if isinstance(data, dict) else {}

    async def delete_document(self, dataset_id: str, document_id: str) -> bool:
        """Delete a document from a dataset."""
        await self._request(
            "DELETE",
            f"/api/v1/datasets/{dataset_id}/documents/{document_id}",
        )
        return True

    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and all of its indexed documents."""
        await self._request(
            "DELETE",
            f"/api/v1/datasets/{dataset_id}",
        )
        return True

    async def retrieve(
        self,
        dataset_ids: Sequence[str],
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Retrieve evidence chunks from one or more datasets."""
        payload = await self._request(
            "POST",
            "/api/v1/retrieval",
            json={
                "dataset_ids": list(dataset_ids),
                "query": query,
                "top_k": top_k,
                "filters": filters or {},
            },
        )
        data = self._unwrap(payload)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("chunks", "results", "documents", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    async def chat_completion(
        self,
        dataset_ids: Sequence[str],
        messages: list[dict[str, Any]],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Run a bounded chat completion against one or more datasets."""
        payload = await self._request(
            "POST",
            "/api/v1/chat",
            json={
                "dataset_ids": list(dataset_ids),
                "messages": messages,
                "top_k": top_k,
                "filters": filters or {},
            },
        )
        data = self._unwrap(payload)
        return data if isinstance(data, dict) else {}

    async def health(self) -> dict[str, Any]:
        """Return the RAGFlow sidecar health payload."""
        payload = await self._request("GET", "/health")
        if isinstance(payload, dict):
            return payload
        return {"status": "unknown"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> Any:
        """Execute an HTTP request with retry/backoff for transient failures."""
        client = await self._get_client()
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                response = await client.request(
                    method,
                    path,
                    json=json,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                if not response.content:
                    return {}
                return response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                log = logger.bind(
                    method=method,
                    path=path,
                    status_code=status_code,
                    attempt=attempt + 1,
                )
                log.error("ragflow_request_failed", error=str(exc))
                if status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                raise
            except Exception as exc:
                logger.error(
                    "ragflow_request_exception",
                    method=method,
                    path=path,
                    attempt=attempt + 1,
                    error=str(exc),
                )
                raise

        raise RuntimeError("unreachable")

    @staticmethod
    def _unwrap(payload: Any) -> Any:
        """Return the nested `data` payload when RAGFlow wraps responses."""
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

"""Async adapter for the synchronous DeepXiv SDK Reader."""

import asyncio
from typing import Any

import structlog

from app.config import settings
from app.exceptions import ExternalAPIError, RateLimitError

logger = structlog.get_logger(__name__)


def _create_reader():
    """Create a DeepXiv Reader instance from settings."""
    from deepxiv_sdk import Reader

    return Reader(
        token=settings.deepxiv_token or None,
        base_url=settings.deepxiv_base_url,
        timeout=settings.deepxiv_timeout,
        max_retries=settings.deepxiv_max_retries,
    )


class DeepXivService:
    """Async wrapper around the synchronous DeepXiv SDK Reader.

    Wraps every synchronous call in ``asyncio.to_thread`` so the FastAPI
    event loop is never blocked.  Normalises the known field inconsistencies
    documented in the SDK's Interface.md (sections list/dict, citation/citations,
    preview/content).
    """

    def __init__(self) -> None:
        self._reader = _create_reader()

    # ── Internal helpers ───────────────────────────────

    async def _run(self, fn, *args, **kwargs) -> Any:
        """Run a synchronous Reader method in a thread, translating exceptions."""
        from deepxiv_sdk import (
            APIError as DxAPIError,
            AuthenticationError as DxAuthError,
            NotFoundError as DxNotFoundError,
            RateLimitError as DxRateLimitError,
        )

        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except DxAuthError as exc:
            logger.warning("deepxiv_auth_error", error=str(exc))
            raise ExternalAPIError("deepxiv", 401, str(exc)) from exc
        except DxRateLimitError as exc:
            logger.warning("deepxiv_rate_limit", error=str(exc))
            raise RateLimitError("deepxiv", retry_after=60) from exc
        except DxNotFoundError:
            return None
        except DxAPIError as exc:
            logger.warning("deepxiv_api_error", error=str(exc))
            raise ExternalAPIError("deepxiv", 502, str(exc)) from exc
        except Exception as exc:
            logger.error("deepxiv_unexpected_error", error=str(exc)[:200])
            raise ExternalAPIError("deepxiv", 502, str(exc)[:200]) from exc

    @staticmethod
    def _normalize_sections(sections: Any) -> list[dict]:
        if isinstance(sections, dict):
            return [{"name": k, **v} for k, v in sections.items()]
        if isinstance(sections, list):
            return sections
        return []

    @staticmethod
    def _normalize_citations(data: dict) -> int:
        return data.get("citations", data.get("citation", 0)) or 0

    @staticmethod
    def _normalize_preview_text(data: dict) -> str:
        return data.get("content") or data.get("preview") or ""

    # ── arXiv search ───────────────────────────────────

    async def search(
        self,
        query: str,
        size: int = 10,
        offset: int = 0,
        search_mode: str = "hybrid",
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        categories: list[str] | None = None,
        authors: list[str] | None = None,
        min_citation: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        result = await self._run(
            self._reader.search,
            query=query,
            size=size,
            offset=offset,
            search_mode=search_mode,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            categories=categories,
            authors=authors,
            min_citation=min_citation,
            date_from=date_from,
            date_to=date_to,
        )
        # Normalize citation field in each result
        for item in (result or {}).get("results", []):
            item["citations"] = self._normalize_citations(item)
        return result or {"total": 0, "results": []}

    # ── Progressive paper reading ──────────────────────

    async def head(self, arxiv_id: str) -> dict | None:
        result = await self._run(self._reader.head, arxiv_id)
        if result:
            result["sections"] = self._normalize_sections(result.get("sections"))
            result["citations"] = self._normalize_citations(result)
        return result

    async def brief(self, arxiv_id: str) -> dict | None:
        result = await self._run(self._reader.brief, arxiv_id)
        if result:
            result["citations"] = self._normalize_citations(result)
        return result

    async def section(self, arxiv_id: str, section_name: str) -> str:
        result = await self._run(self._reader.section, arxiv_id, section_name)
        return result or ""

    async def raw(self, arxiv_id: str) -> str:
        result = await self._run(self._reader.raw, arxiv_id)
        return result or ""

    async def preview(self, arxiv_id: str) -> dict:
        result = await self._run(self._reader.preview, arxiv_id) or {}
        result["text"] = self._normalize_preview_text(result)
        return result

    async def json(self, arxiv_id: str) -> dict:
        return await self._run(self._reader.json, arxiv_id) or {}

    async def markdown_url(self, arxiv_id: str) -> str:
        return self._reader.markdown(arxiv_id)

    # ── PMC ────────────────────────────────────────────

    async def pmc_head(self, pmc_id: str) -> dict | None:
        return await self._run(self._reader.pmc_head, pmc_id)

    async def pmc_full(self, pmc_id: str) -> dict:
        return await self._run(self._reader.pmc_full, pmc_id) or {}

    # ── Trending / social ──────────────────────────────

    async def trending(self, days: int = 7, limit: int = 30) -> dict:
        result = await self._run(self._reader.trending, days=days, limit=limit)
        return result or {"papers": [], "total": 0, "days": days}

    async def social_impact(self, arxiv_id: str) -> dict | None:
        return await self._run(self._reader.social_impact, arxiv_id)

    # ── Web search / Semantic Scholar ──────────────────

    async def websearch(self, query: str) -> dict:
        return await self._run(self._reader.websearch, query) or {}

    async def semantic_scholar(self, s2_id: str) -> dict:
        return await self._run(self._reader.semantic_scholar, s2_id) or {}


def get_deepxiv_service() -> DeepXivService:
    """Factory for route-level dependency injection."""
    return DeepXivService()

"""OpenAlex API client — comprehensive scholarly metadata."""

import httpx
import structlog

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import OPENALEX_LIMITER

logger = structlog.get_logger(__name__)

OPENALEX_BASE_URL = "https://api.openalex.org"


class OpenAlexClient:
    """
    OpenAlex API client.

    - Free, no API key required (polite pool with mailto)
    - Covers 250M+ works with rich metadata
    - Author disambiguation built-in (Author IDs)
    - Provides concepts, topics, citation data
    """

    def __init__(self, mailto: str = ""):
        self.mailto = mailto
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            params = {"mailto": self.mailto} if self.mailto else {}
            self._client = httpx.AsyncClient(
                base_url=OPENALEX_BASE_URL,
                params=params,
                timeout=30.0,
            )
        return self._client

    async def get_work_by_doi(self, doi: str) -> dict:
        """Fetch work metadata by DOI."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(f"/works/doi:{doi}")
                if resp.status_code == 404:
                    return {}
                if resp.status_code == 429:
                    raise RateLimitError("openalex", retry_after=60)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "openalex_api_error", doi=doi, status=e.response.status_code
                )
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def get_work(self, openalex_id: str) -> dict:
        """Fetch work metadata by OpenAlex ID."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(f"/works/{openalex_id}")
                if resp.status_code == 404:
                    return {}
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "openalex_api_error", id=openalex_id, status=e.response.status_code
                )
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def search_works(self, title: str, rows: int = 5) -> list[dict]:
        """Search works by title."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(
                    "/works",
                    params={
                        "search": title,
                        "per_page": rows,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
            except httpx.HTTPStatusError as e:
                logger.error(
                    "openalex_search_error", title=title, status=e.response.status_code
                )
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def get_author(self, openalex_id: str) -> dict:
        """Fetch author profile by OpenAlex ID."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(f"/authors/{openalex_id}")
                if resp.status_code == 404:
                    return {}
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "openalex_author_error",
                    id=openalex_id,
                    status=e.response.status_code,
                )
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def get_citations(self, openalex_id: str, per_page: int = 50) -> list[dict]:
        """Get papers that cite a given work."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(
                    "/works",
                    params={
                        "filter": f"cites:{openalex_id}",
                        "per_page": per_page,
                    },
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except httpx.HTTPStatusError as e:
                logger.error("openalex_citations_error", id=openalex_id)
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def get_references(self, openalex_id: str, per_page: int = 50) -> list[dict]:
        """Get works referenced by a given paper."""
        client = await self._get_client()
        async with OPENALEX_LIMITER:
            try:
                resp = await client.get(
                    "/works",
                    params={
                        "filter": f"cited_by:{openalex_id}",
                        "per_page": per_page,
                    },
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except httpx.HTTPStatusError as e:
                logger.error("openalex_refs_error", id=openalex_id)
                raise ExternalAPIError("openalex", e.response.status_code, str(e))

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

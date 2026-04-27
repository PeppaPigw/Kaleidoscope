"""CrossRef API client — metadata retrieval for DOIs."""

import httpx
import structlog

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import CROSSREF_LIMITER

logger = structlog.get_logger(__name__)

CROSSREF_BASE_URL = "https://api.crossref.org"


class CrossRefClient:
    """
    CrossRef REST API client.

    - Free, no API key required
    - Polite pool: include mailto header for higher rate limits (50 req/s)
    - Returns comprehensive metadata for DOI-indexed publications
    """

    def __init__(self, mailto: str = ""):
        self.mailto = mailto
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": f"Kaleidoscope/0.1 (mailto:{self.mailto})"}
            self._client = httpx.AsyncClient(
                base_url=CROSSREF_BASE_URL,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def get_work(self, doi: str) -> dict:
        """
        Fetch metadata for a single DOI.

        Returns the 'message' object from CrossRef response containing:
        title, author, published-date, container-title (journal), references, etc.
        """
        client = await self._get_client()
        async with CROSSREF_LIMITER:
            try:
                resp = await client.get(
                    f"/works/{doi}",
                    params={"mailto": self.mailto} if self.mailto else {},
                )
                if resp.status_code == 404:
                    return {}
                if resp.status_code == 429:
                    raise RateLimitError("crossref", retry_after=60)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {})
            except httpx.HTTPStatusError as e:
                logger.error(
                    "crossref_api_error", doi=doi, status=e.response.status_code
                )
                raise ExternalAPIError("crossref", e.response.status_code, str(e))

    async def search_works(self, query: str, rows: int = 5) -> list[dict]:
        """
        Search CrossRef for works matching a query string.

        Useful for title-based lookups when DOI is unknown.
        """
        client = await self._get_client()
        async with CROSSREF_LIMITER:
            try:
                resp = await client.get(
                    "/works",
                    params={
                        "query": query,
                        "rows": rows,
                        "select": "DOI,title,author,published-date-parts,"
                        "container-title,type,is-referenced-by-count",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("items", [])
            except httpx.HTTPStatusError as e:
                logger.error(
                    "crossref_search_error", query=query, status=e.response.status_code
                )
                raise ExternalAPIError("crossref", e.response.status_code, str(e))

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

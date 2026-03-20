"""Unpaywall API client — Open Access PDF discovery."""

import structlog
import httpx

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import UNPAYWALL_LIMITER

logger = structlog.get_logger(__name__)

UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2"


class UnpaywallClient:
    """
    Unpaywall API client.

    - Free, requires email for access
    - Find Open Access versions of paywalled papers via DOI
    - Returns best OA PDF location (publisher, repository, preprint)
    """

    def __init__(self, email: str):
        self.email = email
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=UNPAYWALL_BASE_URL,
                timeout=30.0,
            )
        return self._client

    async def get_oa_location(self, doi: str) -> dict:
        """
        Find OA location for a DOI.

        Returns dict with:
        - is_oa: bool
        - best_oa_location: {url, url_for_pdf, host_type, version}
        - oa_locations: list of all OA locations
        """
        client = await self._get_client()
        async with UNPAYWALL_LIMITER:
            try:
                resp = await client.get(
                    f"/{doi}",
                    params={"email": self.email},
                )
                if resp.status_code == 404:
                    return {"is_oa": False}
                if resp.status_code == 429:
                    raise RateLimitError("unpaywall", retry_after=60)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error("unpaywall_error", doi=doi, status=e.response.status_code)
                raise ExternalAPIError("unpaywall", e.response.status_code, str(e))

    async def get_pdf_url(self, doi: str) -> str | None:
        """
        Get the best available PDF URL for a DOI.

        Returns None if no OA version is available.
        """
        data = await self.get_oa_location(doi)
        if not data.get("is_oa"):
            return None

        best = data.get("best_oa_location", {})
        return best.get("url_for_pdf") or best.get("url")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

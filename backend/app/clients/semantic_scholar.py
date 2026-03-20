"""Semantic Scholar API client — academic paper search and metadata."""

import structlog
import httpx

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import SEMANTIC_SCHOLAR_LIMITER

logger = structlog.get_logger(__name__)

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = (
    "paperId,externalIds,title,abstract,year,publicationDate,"
    "venue,referenceCount,citationCount,influentialCitationCount,"
    "isOpenAccess,openAccessPdf,fieldsOfStudy,authors"
)


class SemanticScholarClient:
    """
    Semantic Scholar Academic Graph API client.

    - Free tier: 100 requests per 5 minutes
    - Provides paper metadata, citation data, open access PDF links
    - Includes author disambiguation and influence metrics
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=S2_BASE_URL,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def get_paper(self, paper_id: str, fields: str = S2_FIELDS) -> dict:
        """
        Fetch paper by Semantic Scholar paper ID, DOI, arXiv ID, etc.

        Supported ID formats:
        - S2 Paper ID: "649def34f8be52c8b66281af98ae884c09aef38b"
        - DOI: "DOI:10.18653/v1/N18-3011"
        - arXiv: "arXiv:1705.10311"
        - PMID: "PMID:19872477"
        """
        client = await self._get_client()
        async with SEMANTIC_SCHOLAR_LIMITER:
            try:
                resp = await client.get(
                    f"/paper/{paper_id}",
                    params={"fields": fields},
                )
                if resp.status_code == 404:
                    return {}
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "60"))
                    raise RateLimitError("semantic_scholar", retry_after=retry_after)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error("s2_api_error", paper_id=paper_id, status=e.response.status_code)
                raise ExternalAPIError("semantic_scholar", e.response.status_code, str(e))

    async def search_papers(self, query: str, limit: int = 5) -> list[dict]:
        """Search papers by keyword query."""
        client = await self._get_client()
        async with SEMANTIC_SCHOLAR_LIMITER:
            try:
                resp = await client.get(
                    "/paper/search",
                    params={
                        "query": query,
                        "limit": limit,
                        "fields": S2_FIELDS,
                    },
                )
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "60"))
                    raise RateLimitError("semantic_scholar", retry_after=retry_after)
                resp.raise_for_status()
                return resp.json().get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error("s2_search_error", query=query, status=e.response.status_code)
                raise ExternalAPIError("semantic_scholar", e.response.status_code, str(e))

    async def get_paper_citations(
        self, paper_id: str, limit: int = 50
    ) -> list[dict]:
        """Get papers citing this paper."""
        client = await self._get_client()
        async with SEMANTIC_SCHOLAR_LIMITER:
            try:
                resp = await client.get(
                    f"/paper/{paper_id}/citations",
                    params={"fields": "paperId,title,year,citationCount", "limit": limit},
                )
                resp.raise_for_status()
                return resp.json().get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error("s2_citations_error", paper_id=paper_id)
                raise ExternalAPIError("semantic_scholar", e.response.status_code, str(e))

    async def get_paper_references(
        self, paper_id: str, limit: int = 50
    ) -> list[dict]:
        """Get papers referenced by this paper."""
        client = await self._get_client()
        async with SEMANTIC_SCHOLAR_LIMITER:
            try:
                resp = await client.get(
                    f"/paper/{paper_id}/references",
                    params={"fields": "paperId,title,year,citationCount", "limit": limit},
                )
                resp.raise_for_status()
                return resp.json().get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error("s2_refs_error", paper_id=paper_id)
                raise ExternalAPIError("semantic_scholar", e.response.status_code, str(e))

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

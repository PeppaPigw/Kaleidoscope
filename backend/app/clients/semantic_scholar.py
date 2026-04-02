"""Semantic Scholar API client — academic paper search and metadata."""

import asyncio

import httpx
import structlog

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import SEMANTIC_SCHOLAR_BG_LIMITER, SEMANTIC_SCHOLAR_LIMITER

logger = structlog.get_logger(__name__)

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = (
    "paperId,externalIds,title,abstract,year,publicationDate,"
    "venue,referenceCount,citationCount,influentialCitationCount,"
    "isOpenAccess,openAccessPdf,fieldsOfStudy,authors"
)
# Fields supported by /author/search (aliases not available on search endpoint)
S2_AUTHOR_SEARCH_FIELDS = (
    "authorId,name,affiliations,homepage," "paperCount,citationCount,hIndex,externalIds"
)
# Fields supported by /author/{id} (includes aliases)
S2_AUTHOR_FIELDS = (
    "authorId,name,aliases,affiliations,homepage,"
    "paperCount,citationCount,hIndex,externalIds"
)


class SemanticScholarClient:
    """
    Semantic Scholar Academic Graph API client.

    - Free tier: 100 requests per 5 minutes
    - Provides paper metadata, citation data, open access PDF links
    - Includes author disambiguation and influence metrics

    Pass background=True to use the slower background rate limiter (40/5min)
    so foreground user requests always have quota available.
    """

    def __init__(self, api_key: str = "", background: bool = False):
        self.api_key = api_key
        self._limiter = (
            SEMANTIC_SCHOLAR_BG_LIMITER if background else SEMANTIC_SCHOLAR_LIMITER
        )
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
        async with self._limiter:
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
                logger.error(
                    "s2_api_error", paper_id=paper_id, status=e.response.status_code
                )
                raise ExternalAPIError(
                    "semantic_scholar", e.response.status_code, str(e)
                )

    async def search_papers(self, query: str, limit: int = 5) -> list[dict]:
        """Search papers by keyword query."""
        client = await self._get_client()
        async with self._limiter:
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
                logger.error(
                    "s2_search_error", query=query, status=e.response.status_code
                )
                raise ExternalAPIError(
                    "semantic_scholar", e.response.status_code, str(e)
                )

    async def get_paper_citations(self, paper_id: str, limit: int = 50) -> list[dict]:
        """Get papers citing this paper."""
        client = await self._get_client()
        async with self._limiter:
            try:
                resp = await client.get(
                    f"/paper/{paper_id}/citations",
                    params={
                        "fields": "paperId,title,year,citationCount",
                        "limit": limit,
                    },
                )
                resp.raise_for_status()
                return resp.json().get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error("s2_citations_error", paper_id=paper_id)
                raise ExternalAPIError(
                    "semantic_scholar", e.response.status_code, str(e)
                )

    async def get_paper_references(self, paper_id: str, limit: int = 50) -> list[dict]:
        """Get papers referenced by this paper."""
        client = await self._get_client()
        async with self._limiter:
            try:
                resp = await client.get(
                    f"/paper/{paper_id}/references",
                    params={
                        "fields": "paperId,title,year,citationCount",
                        "limit": limit,
                    },
                )
                resp.raise_for_status()
                return resp.json().get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error("s2_refs_error", paper_id=paper_id)
                raise ExternalAPIError(
                    "semantic_scholar", e.response.status_code, str(e)
                )

    # ── Author API ────────────────────────────────────────────────

    async def search_authors(self, name: str, limit: int = 5) -> list[dict]:
        """Search authors by name. Returns list of candidate author dicts.
        Retries once after waiting if S2 returns 429."""
        client = await self._get_client()
        for attempt in range(2):
            async with self._limiter:
                try:
                    resp = await client.get(
                        "/author/search",
                        params={
                            "query": name,
                            "limit": limit,
                            "fields": S2_AUTHOR_SEARCH_FIELDS,
                        },
                    )
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", "60"))
                        if attempt == 0:
                            logger.warning(
                                "s2_author_search_429_retry",
                                name=name,
                                wait=retry_after,
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(
                            "semantic_scholar", retry_after=retry_after
                        )
                    if resp.status_code == 404:
                        return []
                    resp.raise_for_status()
                    return resp.json().get("data", [])
                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "s2_author_search_error",
                        name=name,
                        status=e.response.status_code,
                    )
                    return []
        return []

    async def get_author(self, s2_author_id: str) -> dict:
        """Fetch full author profile by Semantic Scholar authorId.
        Retries once after waiting if S2 returns 429."""
        client = await self._get_client()
        for attempt in range(2):
            async with self._limiter:
                try:
                    resp = await client.get(
                        f"/author/{s2_author_id}",
                        params={"fields": S2_AUTHOR_FIELDS},
                    )
                    if resp.status_code == 404:
                        return {}
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", "60"))
                        if attempt == 0:
                            logger.warning(
                                "s2_get_author_429_retry",
                                s2_id=s2_author_id,
                                wait=retry_after,
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(
                            "semantic_scholar", retry_after=retry_after
                        )
                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "s2_author_error",
                        s2_id=s2_author_id,
                        status=e.response.status_code,
                    )
                    return {}
        return {}

    async def get_author_papers(
        self,
        s2_author_id: str,
        limit: int = 500,
    ) -> list[dict]:
        """
        Fetch all papers by an author from Semantic Scholar.

        Uses cursor-based pagination to retrieve up to *limit* papers.
        Each paper dict includes: paperId, title, year, citationCount,
        externalIds (ArXiv/DOI), venue, abstract, fieldsOfStudy.
        """
        S2_PAPER_FIELDS = (
            "paperId,title,year,citationCount,externalIds,"
            "venue,publicationVenue,abstract,fieldsOfStudy,isOpenAccess"
        )
        client = await self._get_client()
        results: list[dict] = []
        offset = 0
        page_size = min(100, limit)

        while len(results) < limit:
            for attempt in range(2):
                async with self._limiter:
                    try:
                        resp = await client.get(
                            f"/author/{s2_author_id}/papers",
                            params={
                                "fields": S2_PAPER_FIELDS,
                                "limit": page_size,
                                "offset": offset,
                            },
                        )
                        if resp.status_code == 404:
                            return results
                        if resp.status_code == 429:
                            retry_after = int(resp.headers.get("Retry-After", "60"))
                            if attempt == 0:
                                await asyncio.sleep(retry_after)
                                continue
                            return results
                        resp.raise_for_status()
                        data = resp.json()
                        page = data.get("data", [])
                        results.extend(page)
                        # No more pages
                        if len(page) < page_size or data.get("next") is None:
                            return results
                        offset += len(page)
                        break
                    except httpx.HTTPStatusError as e:
                        logger.warning(
                            "s2_author_papers_error",
                            s2_id=s2_author_id,
                            status=e.response.status_code,
                        )
                        return results
            else:
                return results

        return results

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

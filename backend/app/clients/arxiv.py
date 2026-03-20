"""arXiv API client — preprint metadata and PDF retrieval."""

import re

import structlog
import httpx

from app.exceptions import ExternalAPIError, RateLimitError
from app.utils.rate_limiter import ARXIV_LIMITER

logger = structlog.get_logger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivClient:
    """
    arXiv API client.

    - Free, rate limit: 1 request per 3 seconds
    - Returns Atom XML feed
    - PDF URLs can be constructed from arXiv IDs
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_paper(self, arxiv_id: str) -> dict:
        """
        Fetch metadata for an arXiv paper.

        Returns structured dict with title, abstract, authors, categories, etc.
        """
        client = await self._get_client()
        async with ARXIV_LIMITER:
            try:
                resp = await client.get(
                    ARXIV_API_URL,
                    params={"id_list": arxiv_id, "max_results": 1},
                )
                resp.raise_for_status()
                return self._parse_atom_entry(resp.text)
            except httpx.HTTPStatusError as e:
                logger.error("arxiv_api_error", arxiv_id=arxiv_id, status=e.response.status_code)
                raise ExternalAPIError("arxiv", e.response.status_code, str(e))

    @staticmethod
    def _parse_atom_entry(xml_text: str) -> dict:
        """Parse arXiv Atom XML response into a structured dict."""
        from lxml import etree

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        root = etree.fromstring(xml_text.encode())
        entries = root.findall("atom:entry", ns)
        if not entries:
            return {}

        entry = entries[0]

        # Extract arXiv ID from entry id URL
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id_match = re.search(r"abs/(.+?)(?:v\d+)?$", entry_id)
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else ""

        # Authors
        authors = []
        for author_elem in entry.findall("atom:author", ns):
            name = author_elem.findtext("atom:name", default="", namespaces=ns)
            affiliation = author_elem.findtext("arxiv:affiliation", default="", namespaces=ns)
            authors.append({"name": name, "affiliation": affiliation})

        # Categories
        categories = [
            cat.get("term", "")
            for cat in entry.findall("atom:category", ns)
            if cat.get("term")
        ]

        # DOI (if present)
        doi = entry.findtext("arxiv:doi", default=None, namespaces=ns)

        return {
            "arxiv_id": arxiv_id,
            "title": (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " "),
            "abstract": (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip(),
            "authors": authors,
            "categories": categories,
            "published": entry.findtext("atom:published", default="", namespaces=ns),
            "updated": entry.findtext("atom:updated", default="", namespaces=ns),
            "doi": doi,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None,
            "abs_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
        }

    @staticmethod
    def construct_pdf_url(arxiv_id: str) -> str:
        """Construct PDF URL from arXiv ID."""
        clean_id = arxiv_id.replace("arXiv:", "").strip()
        return f"https://arxiv.org/pdf/{clean_id}.pdf"

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

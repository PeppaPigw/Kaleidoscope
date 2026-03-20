"""Keyword search service via Meilisearch."""

import time

import meilisearch
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Meilisearch index configuration
PAPERS_INDEX = "papers"
SEARCHABLE_ATTRIBUTES = ["title", "abstract", "keywords", "author_names"]
FILTERABLE_ATTRIBUTES = ["year", "venue", "paper_type", "oa_status", "has_full_text"]
SORTABLE_ATTRIBUTES = ["year", "citation_count", "created_at"]


class KeywordSearchService:
    """
    Full-text keyword search via Meilisearch.

    Provides fast, typo-tolerant keyword search with faceted filtering.
    """

    def __init__(self) -> None:
        self.client = meilisearch.Client(
            settings.meili_url,
            settings.meili_master_key,
        )
        self._index_initialized = False

    def _ensure_index(self) -> None:
        """Ensure the papers index exists with correct settings."""
        if self._index_initialized:
            return

        try:
            self.client.create_index(PAPERS_INDEX, {"primaryKey": "id"})
        except meilisearch.errors.MeilisearchApiError:
            pass  # Index already exists

        index = self.client.index(PAPERS_INDEX)
        index.update_searchable_attributes(SEARCHABLE_ATTRIBUTES)
        index.update_filterable_attributes(FILTERABLE_ATTRIBUTES)
        index.update_sortable_attributes(SORTABLE_ATTRIBUTES)

        self._index_initialized = True
        logger.info("meilisearch_index_configured", index=PAPERS_INDEX)

    def search(
        self,
        query: str,
        filters: dict | None = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str | None = None,
        order: str = "desc",
    ) -> dict:
        """
        Search papers by keyword.

        Returns dict with hits, total, and processing time.
        """
        self._ensure_index()
        index = self.client.index(PAPERS_INDEX)

        start = time.monotonic()

        # Build filter string
        filter_parts = []
        if filters:
            if filters.get("year_from"):
                filter_parts.append(f"year >= {filters['year_from']}")
            if filters.get("year_to"):
                filter_parts.append(f"year <= {filters['year_to']}")
            if filters.get("venue"):
                filter_parts.append(f'venue = "{filters["venue"]}"')
            if filters.get("paper_type"):
                filter_parts.append(f'paper_type = "{filters["paper_type"]}"')
            if filters.get("oa_status"):
                filter_parts.append(f'oa_status = "{filters["oa_status"]}"')
            if filters.get("has_full_text") is not None:
                filter_parts.append(f"has_full_text = {str(filters['has_full_text']).lower()}")

        search_params: dict = {
            "offset": (page - 1) * per_page,
            "limit": per_page,
            "attributesToHighlight": ["title", "abstract"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>",
        }

        if filter_parts:
            search_params["filter"] = " AND ".join(filter_parts)

        if sort_by and sort_by != "relevance":
            search_params["sort"] = [f"{sort_by}:{order}"]

        result = index.search(query, search_params)

        elapsed = (time.monotonic() - start) * 1000

        return {
            "hits": result.get("hits", []),
            "total": result.get("estimatedTotalHits", 0),
            "page": page,
            "per_page": per_page,
            "processing_time_ms": elapsed,
        }

    def index_paper(self, paper_doc: dict) -> None:
        """
        Index a single paper document.

        Expected paper_doc format:
        {
            "id": "uuid-string",
            "title": "...",
            "abstract": "...",
            "keywords": ["..."],
            "author_names": ["Author A", "Author B"],
            "year": 2024,
            "venue": "Nature",
            "paper_type": "article",
            "oa_status": "gold",
            "has_full_text": True,
            "citation_count": 42,
            "created_at": 1710000000,
        }
        """
        self._ensure_index()
        index = self.client.index(PAPERS_INDEX)
        index.add_documents([paper_doc])
        logger.debug("meilisearch_indexed", paper_id=paper_doc.get("id"))

    def index_papers_batch(self, papers: list[dict]) -> None:
        """Index multiple papers in one batch."""
        if not papers:
            return
        self._ensure_index()
        index = self.client.index(PAPERS_INDEX)
        index.add_documents(papers)
        logger.info("meilisearch_batch_indexed", count=len(papers))

    def delete_paper(self, paper_id: str) -> None:
        """Remove a paper from the search index."""
        self._ensure_index()
        index = self.client.index(PAPERS_INDEX)
        index.delete_document(paper_id)

"""Hybrid search — combine keyword + semantic search via Reciprocal Rank Fusion."""

import time

import structlog

from app.services.search.keyword_search import KeywordSearchService
from app.services.search.vector_search import VectorSearchService

logger = structlog.get_logger(__name__)

# RRF constant — higher values weight all positions more equally
RRF_K = 60


class HybridSearchService:
    """
    Combine keyword search (Meilisearch) and semantic search (Qdrant)
    using Reciprocal Rank Fusion (RRF).

    RRF formula: score(d) = Σ 1 / (k + rank_i(d))

    This produces a unified ranking that benefits from both exact keyword
    matches and semantic meaning.
    """

    def __init__(
        self,
        keyword_service: KeywordSearchService,
        vector_service: VectorSearchService,
    ):
        self.keyword = keyword_service
        self.vector = vector_service

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        filters: dict | None = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "relevance",
        order: str = "desc",
    ) -> dict:
        """
        Execute search in the specified mode.

        Modes:
        - keyword: Meilisearch only (fast, typo-tolerant)
        - semantic: Qdrant only (meaning-based)
        - hybrid: RRF fusion of both (best quality)
        """
        start = time.monotonic()

        if mode == "keyword":
            result = self.keyword.search(query, filters, page, per_page, sort_by, order)
            result["mode"] = "keyword"
            return result

        if mode == "semantic":
            vector_results = self.vector.search(query, top_k=per_page * page, filters=filters)
            # Paginate vector results
            start_idx = (page - 1) * per_page
            page_results = vector_results[start_idx : start_idx + per_page]

            return {
                "hits": [
                    {
                        "paper_id": r["paper_id"],
                        "score": r["score"],
                        "title": r.get("payload", {}).get("title", ""),
                        **{k: v for k, v in (r.get("payload") or {}).items() if k != "paper_id"},
                    }
                    for r in page_results
                ],
                "total": len(vector_results),
                "page": page,
                "per_page": per_page,
                "mode": "semantic",
                "processing_time_ms": (time.monotonic() - start) * 1000,
            }

        # --- Hybrid mode: RRF fusion ---
        # Fetch more results than needed for better fusion
        fetch_size = per_page * 3

        # 1. Keyword search
        kw_result = self.keyword.search(query, filters, 1, fetch_size, sort_by=None, order="desc")
        kw_hits = kw_result.get("hits", [])

        # 2. Vector search
        vec_hits = self.vector.search(query, top_k=fetch_size, filters=filters)

        # 3. RRF Fusion
        scores: dict[str, float] = {}
        paper_data: dict[str, dict] = {}

        # Score keyword results
        for rank, hit in enumerate(kw_hits):
            pid = hit.get("id", hit.get("paper_id", ""))
            if not pid:
                continue
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (RRF_K + rank + 1)
            paper_data[pid] = hit

        # Score vector results
        for rank, hit in enumerate(vec_hits):
            pid = hit.get("paper_id", "")
            if not pid:
                continue
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (RRF_K + rank + 1)
            if pid not in paper_data:
                paper_data[pid] = {
                    "paper_id": pid,
                    "title": hit.get("payload", {}).get("title", ""),
                }

        # Sort by RRF score
        sorted_ids = sorted(scores, key=lambda pid: scores[pid], reverse=True)

        # Paginate
        start_idx = (page - 1) * per_page
        page_ids = sorted_ids[start_idx : start_idx + per_page]

        hits = []
        for pid in page_ids:
            data = paper_data[pid]
            data["score"] = scores[pid]
            data["paper_id"] = pid
            hits.append(data)

        elapsed = (time.monotonic() - start) * 1000

        logger.info(
            "hybrid_search_complete",
            query=query[:50],
            kw_hits=len(kw_hits),
            vec_hits=len(vec_hits),
            rrf_total=len(sorted_ids),
            time_ms=f"{elapsed:.1f}",
        )

        return {
            "hits": hits,
            "total": len(sorted_ids),
            "page": page,
            "per_page": per_page,
            "mode": "hybrid",
            "processing_time_ms": elapsed,
        }

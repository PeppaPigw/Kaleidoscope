"""Search API routes — keyword, semantic, and hybrid search."""

import structlog
from fastapi import APIRouter, Query

from app.schemas.search import SearchHit, SearchResponse
from app.services.search.keyword_search import KeywordSearchService
from app.services.search.vector_search import VectorSearchService
from app.services.search.hybrid_search import HybridSearchService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/search", tags=["search"])

# Service instances (singleton for the app lifecycle)
_keyword_service = KeywordSearchService()
_vector_service = VectorSearchService()
_hybrid_service = HybridSearchService(_keyword_service, _vector_service)


@router.get("", response_model=SearchResponse)
async def search_papers(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    mode: str = Query("hybrid", description="keyword, semantic, or hybrid"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    year_from: int | None = Query(None, description="Filter: minimum year"),
    year_to: int | None = Query(None, description="Filter: maximum year"),
    venue: str | None = Query(None, description="Filter: venue name"),
    paper_type: str | None = Query(None, description="Filter: article, review, preprint"),
    oa_status: str | None = Query(None, description="Filter: gold, green, bronze, closed"),
    has_full_text: bool | None = Query(None, description="Filter: has full-text PDF"),
    sort_by: str = Query("relevance", description="Sort: relevance, year, citation_count"),
    order: str = Query("desc", description="Sort order: asc or desc"),
):
    """
    Search papers using keyword, semantic, or hybrid mode.

    - **keyword**: Fast, typo-tolerant full-text search via Meilisearch
    - **semantic**: Meaning-based search via SPECTER2 embeddings + Qdrant
    - **hybrid**: Best of both via Reciprocal Rank Fusion (recommended)
    """
    logger.info("search_request", query=q[:50], mode=mode)

    filters = {
        "year_from": year_from,
        "year_to": year_to,
        "venue": venue,
        "paper_type": paper_type,
        "oa_status": oa_status,
        "has_full_text": has_full_text,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    result = _hybrid_service.search(
        query=q,
        mode=mode,
        filters=filters if filters else None,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
    )

    # Transform hits to response schema
    hits = []
    for hit in result.get("hits", []):
        hits.append(
            SearchHit(
                paper_id=hit.get("paper_id", hit.get("id", "")),
                doi=hit.get("doi"),
                arxiv_id=hit.get("arxiv_id"),
                title=hit.get("title", ""),
                abstract=hit.get("abstract"),
                published_at=hit.get("published_at"),
                citation_count=hit.get("citation_count"),
                authors=hit.get("author_names", []),
                venue=hit.get("venue"),
                score=hit.get("score", 0.0),
                highlights=hit.get("_formatted"),
            )
        )

    return SearchResponse(
        hits=hits,
        total=result.get("total", 0),
        page=page,
        per_page=per_page,
        query=q,
        mode=mode,
        processing_time_ms=result.get("processing_time_ms", 0.0),
    )

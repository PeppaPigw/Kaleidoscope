"""Process-level singleton search service instances.

All code paths that need search services should import from here
to avoid redundant model loading (SPECTER2 is ~500MB).

Usage:
    from app.services.search.instances import vector_service, keyword_service, hybrid_service
"""

from app.services.search.hybrid_search import HybridSearchService
from app.services.search.keyword_search import KeywordSearchService
from app.services.search.vector_search import VectorSearchService

# Process-level singletons — created once, reused across all requests
keyword_service = KeywordSearchService()
vector_service = VectorSearchService()
hybrid_service = HybridSearchService(keyword_service, vector_service)

"""Query router — classify and route queries to the right retrieval backend."""

from __future__ import annotations

import re
import time
from enum import Enum
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.ragflow.ragflow_query_service import RagflowQueryService
from app.services.search.instances import hybrid_service

logger = structlog.get_logger(__name__)


class QueryRoute(str, Enum):
    """Possible retrieval backends for a query."""

    DISCOVERY = "discovery"
    BOUNDED_QA = "bounded_qa"
    GRAPH = "graph"
    COMBINED = "combined"


# ── lightweight heuristic patterns ──────────────────────────────────
_GRAPH_PATTERNS = re.compile(
    r"\b(cit(?:e[sd]?|ation|ing)|co-cit|co.citation|bibliographic|"
    r"author.?network|expert|bridge.?paper|graph|path.?between|"
    r"who\s+(?:wrote|authored|cit)|relationship)\b",
    re.IGNORECASE,
)
_QA_PATTERNS = re.compile(
    r"\b(what|how|why|explain|summarize|compare|evidence|"
    r"does|is\s+there|according\s+to|based\s+on)\b",
    re.IGNORECASE,
)
_TREND_PATTERNS = re.compile(
    r"\b(trend|evolution|growth|decline|over.?time|timeline|"
    r"historic|year|annual|decade)\b",
    re.IGNORECASE,
)


class QueryRouter:
    """Classify queries and dispatch to the right backend."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ragflow = RagflowQueryService(db)

    def classify(
        self,
        query: str,
        *,
        collection_id: str | None = None,
        paper_id: str | None = None,
    ) -> QueryRoute:
        """Classify a query into a route using lightweight heuristics."""
        q = query.strip()

        # If the user scoped to a collection → bounded QA via RAGFlow
        if collection_id:
            return QueryRoute.BOUNDED_QA

        # If the user scoped to a specific paper → bounded QA
        if paper_id:
            return QueryRoute.BOUNDED_QA

        # Graph-shaped queries
        if _GRAPH_PATTERNS.search(q):
            return QueryRoute.GRAPH

        # Trend/analytics queries → combined (graph + search)
        if _TREND_PATTERNS.search(q):
            return QueryRoute.COMBINED

        # Direct question → bounded QA if RAGFlow is enabled
        if _QA_PATTERNS.search(q) and settings.ragflow_sync_enabled:
            return QueryRoute.BOUNDED_QA

        # Default → discovery (hybrid search)
        return QueryRoute.DISCOVERY

    async def route(
        self,
        query: str,
        *,
        collection_id: str | None = None,
        paper_id: str | None = None,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classify and execute query against the appropriate backend."""
        started = time.perf_counter()
        route = self.classify(
            query,
            collection_id=collection_id,
            paper_id=paper_id,
        )
        log = logger.bind(query=query[:80], route=route.value)

        try:
            if route == QueryRoute.BOUNDED_QA:
                result = await self._bounded_qa(
                    query,
                    collection_id,
                    paper_id,
                    top_k,
                )
            elif route == QueryRoute.GRAPH:
                result = await self._graph_query(query, top_k)
            elif route == QueryRoute.COMBINED:
                result = await self._combined_query(
                    query,
                    top_k,
                    filters,
                )
            else:
                result = await self._discovery(query, top_k, filters)
        except Exception as exc:  # noqa: BLE001
            log.error("query_router_failed", error=str(exc))
            result = {
                "hits": [],
                "answer": None,
                "sources": [],
                "error": "query_processing_failed",
            }

        latency_ms = (time.perf_counter() - started) * 1000
        result["route"] = route.value
        result["latency_ms"] = round(latency_ms, 1)
        log.info(
            "query_routed",
            latency_ms=round(latency_ms, 1),
            hit_count=len(result.get("hits", [])),
        )
        return result

    # ── backend dispatchers ─────────────────────────────────────────

    async def _bounded_qa(
        self,
        query: str,
        collection_id: str | None,
        paper_id: str | None,
        top_k: int,
    ) -> dict[str, Any]:
        """Route bounded Q&A to RAGFlow sidecar."""
        if collection_id:
            return await self.ragflow.ask_workspace(
                collection_id,
                query,
                top_k,
            )
        if paper_id:
            return await self.ragflow.ask_paper(paper_id, query, top_k)
        # Fallback: treat as discovery
        return await self._discovery(query, top_k, None)

    async def _graph_query(
        self,
        query: str,
        top_k: int,
    ) -> dict[str, Any]:
        """Route graph-shaped queries to Neo4j via CitationGraphService."""
        from app.services.graph.citation_graph import CitationGraphService

        graph = CitationGraphService(self.db)
        stats = await graph.get_stats()
        return {
            "hits": [],
            "answer": None,
            "sources": [],
            "graph_stats": stats,
            "hint": "Use /api/v1/graph/* endpoints for citations",
        }

    async def _discovery(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Route discovery queries to hybrid search."""
        result = hybrid_service.search(
            query,
            mode="hybrid",
            filters=filters,
            per_page=top_k,
        )
        return {
            "hits": result.get("hits", []),
            "answer": None,
            "sources": [],
            "total": result.get("total", 0),
            "mode_used": result.get("mode_used", "hybrid"),
        }

    async def _combined_query(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Combine discovery search with graph expansion."""
        discovery = await self._discovery(query, top_k, filters)
        top_ids = [
            h.get("paper_id", h.get("id", "")) for h in discovery.get("hits", [])[:5]
        ]

        # Expand top hits via graph neighborhood
        from app.services.graph.citation_graph import CitationGraphService

        graph = CitationGraphService(self.db)
        expanded: list[dict[str, Any]] = []
        for pid in top_ids:
            if not pid:
                continue
            try:
                nbr = await graph.get_neighborhood(pid, depth=1)
                expanded.append(nbr)
            except Exception:  # noqa: BLE001
                pass

        discovery["graph_expansion"] = expanded
        return discovery

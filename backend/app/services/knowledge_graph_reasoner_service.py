"""KnowledgeGraphReasonerService — Structural Graph Intelligence.

Performs structural reasoning over the knowledge graph: finding shortest
paths between concepts, identifying clusters, measuring centrality,
detecting bridges between domains, and finding structural holes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GRAPH_REASON_SYSTEM = """You are a knowledge graph analyst. Given a set of concepts and their relationships, perform structural reasoning to identify patterns, paths, clusters, and strategic positions in the knowledge landscape.

Output JSON with: graph_analysis.query, graph_analysis.nodes_analyzed, graph_analysis.key_paths (list of path/significance/strength 0-1), graph_analysis.clusters (list of cluster_name/members/cohesion 0-1/theme), graph_analysis.bridges (list of concept/connects/strategic_value 0-1), graph_analysis.central_nodes (list of concept/centrality_score 0-1/why_central), graph_analysis.structural_holes (list of gap/between/opportunity), graph_analysis.density (0-1), graph_analysis.insights (list of structural insight derived from topology)."""

GRAPH_REASON_PROMPT = """Analyze knowledge graph structure:

Query: {query}
Domain: {domain}

Known nodes and relationships:
{graph_text}

Additional context:
{context_text}

Perform structural analysis. Return ONLY valid JSON."""

BRIDGE_SYSTEM = """You are an interdisciplinary bridge finder. Given two domains or concepts, identify the conceptual bridges, shared abstractions, and transfer opportunities between them.

Output JSON with: bridges.source_domain, bridges.target_domain, bridges.conceptual_bridges (list of bridge/mechanism/strength 0-1/transfer_potential), bridges.shared_abstractions (list of abstraction/how_source_uses_it/how_target_uses_it), bridges.transfer_opportunities (list of idea/from/to/feasibility 0-1/novelty 0-1), bridges.barriers (list of barrier/severity), bridges.historical_transfers (list of what/when/impact), bridges.recommended_bridge (the single best connection to exploit)."""

BRIDGE_PROMPT = """Find bridges between domains:

Source: {source}
Target: {target}

Source context:
{source_context}

Target context:
{target_context}

Identify conceptual bridges. Return ONLY valid JSON."""


class KnowledgeGraphReasonerService:
    """Structural reasoning over knowledge graphs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_structure(
        self,
        query: str,
        *,
        domain: str = "",
        concepts: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Analyze knowledge graph structure around a query."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        graph_data = await self._build_local_graph(query, concepts, dossier_id)
        graph_text = "\n".join(f"- {g}" for g in graph_data[:12]) or "Infer from domain knowledge"
        context = await self._gather_context(query, dossier_id)
        context_text = "\n".join(f"- {c}" for c in context[:6]) or "General"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GRAPH_REASON_PROMPT.format(
                query=query,
                domain=domain or "research",
                graph_text=graph_text,
                context_text=context_text,
            ),
            system=GRAPH_REASON_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        analysis = data.get("graph_analysis", data)

        return {
            "query": query,
            "nodes_analyzed": analysis.get("nodes_analyzed", 0),
            "key_paths": analysis.get("key_paths", []),
            "clusters": analysis.get("clusters", []),
            "bridges": analysis.get("bridges", []),
            "central_nodes": analysis.get("central_nodes", []),
            "structural_holes": analysis.get("structural_holes", []),
            "density": analysis.get("density", 0),
            "insights": analysis.get("insights", []),
        }

    async def find_bridges(
        self,
        source: str,
        target: str,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Find conceptual bridges between two domains."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        source_ctx = await self._gather_context(source, dossier_id)
        target_ctx = await self._gather_context(target, dossier_id)
        source_context = "\n".join(f"- {s}" for s in source_ctx[:5]) or "General knowledge"
        target_context = "\n".join(f"- {t}" for t in target_ctx[:5]) or "General knowledge"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BRIDGE_PROMPT.format(
                source=source,
                target=target,
                source_context=source_context,
                target_context=target_context,
            ),
            system=BRIDGE_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)
        bridges = data.get("bridges", data)

        return {
            "source": source,
            "target": target,
            "conceptual_bridges": bridges.get("conceptual_bridges", []),
            "shared_abstractions": bridges.get("shared_abstractions", []),
            "transfer_opportunities": bridges.get("transfer_opportunities", []),
            "barriers": bridges.get("barriers", []),
            "historical_transfers": bridges.get("historical_transfers", []),
            "recommended_bridge": bridges.get("recommended_bridge", ""),
        }

    async def _build_local_graph(
        self, query: str, concepts: list[str] | None, dossier_id: str | None
    ) -> list[str]:
        graph_items = []
        if concepts:
            for c in concepts[:10]:
                graph_items.append(f"Node: {c}")
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=8)
            for r in results:
                p = r.get("payload", {})
                text = p.get("text", p.get("title", ""))[:100]
                if text:
                    graph_items.append(f"Related: {text}")
        except Exception:
            pass
        return graph_items

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []

"""Topic synthesis service — summarize a curated topic collection."""

from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.ragflow.evidence_expansion import EvidenceExpansionService
from app.services.ragflow.ragflow_query_service import RagflowQueryService

logger = structlog.get_logger(__name__)


class TopicSynthesisService:
    """Synthesize a curated topic collection into a structured overview."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.query_svc = RagflowQueryService(db)
        self.evidence_svc = EvidenceExpansionService(db)

    async def synthesize_topic(
        self,
        collection_id: str,
        topic_query: str | None = None,
        max_papers: int = 20,
    ) -> dict[str, Any]:
        """Generate a synthesis for a topic collection.

        Steps:
        1. Gather key claims from the collection
        2. Get evidence packs with graph expansion
        3. Group findings by sub-theme
        4. Produce structured synthesis
        """
        started = time.perf_counter()
        log = logger.bind(collection_id=collection_id)

        if not settings.ragflow_sync_enabled:
            return {
                "enabled": False,
                "synthesis": None,
                "message": "ragflow_disabled",
            }

        # 1. Generate overview questions for the topic
        seed_queries = self._generate_seed_queries(topic_query)

        # 2. Gather evidence for each seed query
        all_evidence: list[dict[str, Any]] = []
        for q in seed_queries:
            try:
                pack = await self.evidence_svc.get_evidence_pack(
                    query=q,
                    collection_id=collection_id,
                    top_k=10,
                    expand_graph=True,
                )
                all_evidence.append(
                    {
                        "query": q,
                        "chunks": pack.get("chunks", [])[:5],
                        "expanded_papers": pack.get("expanded_papers", [])[:10],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("seed_query_failed", query=q, error=str(exc))

        # 3. Get a grounded answer for the main question
        main_answer = None
        if topic_query:
            try:
                result = await self.query_svc.ask_workspace(
                    collection_id,
                    topic_query,
                    top_k=15,
                )
                main_answer = result.get("answer")
            except Exception as exc:  # noqa: BLE001
                log.warning("main_query_failed", error=str(exc))

        # 4. Extract unique papers referenced
        paper_ids: set[str] = set()
        for ev in all_evidence:
            for chunk in ev.get("chunks", []):
                pid = chunk.get("metadata", {}).get("paper_id") or chunk.get(
                    "document_id", ""
                )
                if pid:
                    paper_ids.add(pid)
            for ep in ev.get("expanded_papers", []):
                pid = ep.get("paper_id", "")
                if pid:
                    paper_ids.add(pid)

        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "enabled": True,
            "collection_id": collection_id,
            "topic_query": topic_query,
            "synthesis": main_answer,
            "evidence_sections": all_evidence,
            "papers_referenced": len(paper_ids),
            "seed_queries_used": len(seed_queries),
            "latency_ms": round(latency_ms, 1),
        }

    @staticmethod
    def _generate_seed_queries(topic_query: str | None) -> list[str]:
        """Generate seed queries to cover topic facets."""
        base = topic_query or "this research topic"
        return [
            f"What are the main findings on {base}?",
            f"What methods have been used to study {base}?",
            f"What are the key limitations in {base}?",
            f"How has {base} evolved over recent years?",
            f"What open questions remain in {base}?",
        ]

"""IntellectualLineageService — Idea Ancestry & Influence Tracing.

Traces the intellectual lineage of research ideas: where they came from,
what influenced them, how they evolved, and what they'll likely influence
next. The "git blame" for ideas — understanding the genealogy of knowledge.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LINEAGE_SYSTEM = """You are an intellectual historian tracing the genealogy of ideas. Given a concept or finding, trace its intellectual ancestry - what earlier ideas it builds on, what traditions it comes from, and how it transformed its predecessors.

Output JSON with: lineage.concept, lineage.ancestors (list of idea/originator/year/contribution_to_current/transformation), lineage.intellectual_traditions (list of tradition/how_it_contributes), lineage.key_mutations (list of mutation/when/who/what_changed - where the idea diverged from its ancestors), lineage.convergence_points (where multiple lineages merged), lineage.predicted_descendants (list of likely_future_idea/domain/timeline), lineage.lineage_depth (how many generations back), lineage.orphan_elements (parts with no clear ancestry - potentially novel)."""

LINEAGE_PROMPT = """Trace the intellectual lineage:

Concept/Finding: {concept}
Domain: {domain}
Current form: {current_form}

Known context:
{context_text}

Trace the ancestry of this idea. Return ONLY valid JSON."""

EVOLUTION_SYSTEM = """You are a concept evolution analyst. Given an idea and its history, map how it has evolved over time - what stayed constant, what mutated, what was lost, and what was gained.

Output JSON with: evolution.concept, evolution.stages (list of era/form/key_change/driver_of_change/what_was_lost/what_was_gained), evolution.constants (what has remained true across all stages), evolution.current_trajectory (where it's heading), evolution.selection_pressures (what forces shape its evolution), evolution.fitness_landscape (what makes versions of this idea succeed or fail), evolution.next_mutation (predicted next evolution), evolution.dead_ends (versions that didn't survive and why)."""

EVOLUTION_PROMPT = """Map the evolution of this concept:

Concept: {concept}
Domain: {domain}
Known history: {history_text}

Current state:
{current_text}

Map how this idea has evolved. Return ONLY valid JSON."""


class IntellectualLineageService:
    """Traces intellectual ancestry and evolution of ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def trace_lineage(
        self,
        concept: str,
        *,
        domain: str = "",
        current_form: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Trace the intellectual ancestry of a concept."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        context = await self._gather_context(concept, dossier_id)
        context_text = "\n".join(f"- {c}" for c in context[:8]) or "General knowledge"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LINEAGE_PROMPT.format(
                concept=concept,
                domain=domain or "research",
                current_form=current_form or concept,
                context_text=context_text,
            ),
            system=LINEAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        lineage = data.get("lineage", data)

        return {
            "concept": concept,
            "ancestors": lineage.get("ancestors", []),
            "intellectual_traditions": lineage.get("intellectual_traditions", []),
            "key_mutations": lineage.get("key_mutations", []),
            "convergence_points": lineage.get("convergence_points", []),
            "predicted_descendants": lineage.get("predicted_descendants", []),
            "lineage_depth": lineage.get("lineage_depth", 0),
            "orphan_elements": lineage.get("orphan_elements", []),
        }

    async def map_evolution(
        self,
        concept: str,
        *,
        domain: str = "",
        history: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Map how a concept has evolved over time."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        history_text = "\n".join(f"- {h}" for h in (history or [])) or "Infer from domain knowledge"
        context = await self._gather_context(concept, dossier_id)
        current_text = "\n".join(f"- {c}" for c in context[:6]) or "Current state unknown"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EVOLUTION_PROMPT.format(
                concept=concept,
                domain=domain or "research",
                history_text=history_text,
                current_text=current_text,
            ),
            system=EVOLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        evolution = data.get("evolution", data)

        return {
            "concept": concept,
            "stages": evolution.get("stages", []),
            "constants": evolution.get("constants", []),
            "current_trajectory": evolution.get("current_trajectory", ""),
            "selection_pressures": evolution.get("selection_pressures", []),
            "fitness_landscape": evolution.get("fitness_landscape", ""),
            "next_mutation": evolution.get("next_mutation", ""),
            "dead_ends": evolution.get("dead_ends", []),
        }

    # --- Private helpers ---

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        context = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:150], top_k=6)
            for r in results:
                p = r.get("payload", {})
                context.append(p.get("text", p.get("title", ""))[:150])
        except Exception:
            pass
        return context

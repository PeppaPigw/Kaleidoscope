"""InsightCrystallizerService — The "So What?" Engine.

Distills complex multi-source intelligence into crystallized insights.
Takes outputs from multiple engines and produces the single most important
takeaway, the key decision it enables, and the confidence-weighted action.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CRYSTALLIZE_SYSTEM = """You are an insight crystallizer. Given multiple pieces of research intelligence (claims, evidence, analyses), distill them into the single most important insight - the "so what?" that matters most for decision-making.

A great crystallized insight is: surprising (not obvious from any single input), actionable (enables a specific decision), well-supported (grounded in evidence), and concise (one sentence core).

Output JSON with: crystal.core_insight (one sentence - the most important thing), crystal.why_it_matters (2-3 sentences on implications), crystal.confidence (0-1), crystal.evidence_base (list of source/claim/strength 0-1), crystal.decisions_enabled (list of decision/recommended_action/urgency high|medium|low), crystal.what_changes (what should be done differently now), crystal.caveats (list of caveat/severity), crystal.novelty (0-1 how surprising this is vs prior knowledge), crystal.next_question (the most important follow-up question)."""

CRYSTALLIZE_PROMPT = """Crystallize the most important insight from this intelligence:

Research question: {question}
Domain: {domain}

Intelligence gathered:
{intelligence_text}

What is the single most important insight? Return ONLY valid JSON."""

SYNTHESIZE_SYSTEM = """You are a multi-engine synthesis expert. Given outputs from different analytical engines (debate, peer review, replication analysis, impact forecast, etc.), synthesize them into a coherent picture that no single engine could produce alone.

Output JSON with: synthesis.overall_assessment, synthesis.convergence (where engines agree), synthesis.divergence (where engines disagree and why), synthesis.emergent_insights (insights that only appear from combining engines), synthesis.confidence_landscape (which aspects are well-supported vs uncertain), synthesis.recommended_focus (where to direct attention next), synthesis.meta_confidence (0-1 confidence in the synthesis itself)."""

SYNTHESIZE_PROMPT = """Synthesize these multi-engine outputs:

Topic: {topic}

Engine outputs:
{engines_text}

Synthesize into a coherent picture. Return ONLY valid JSON."""


class InsightCrystallizerService:
    """Distills complex intelligence into crystallized insights."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def crystallize(
        self,
        question: str,
        intelligence: list[str],
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Distill multiple intelligence pieces into the single most important insight."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(question, dossier_id)
        all_intel = intelligence + extra
        intelligence_text = "\n".join(f"- {i}" for i in all_intel[:12])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CRYSTALLIZE_PROMPT.format(
                question=question,
                domain=domain or "research",
                intelligence_text=intelligence_text,
            ),
            system=CRYSTALLIZE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        crystal = data.get("crystal", data)

        return {
            "core_insight": crystal.get("core_insight", ""),
            "why_it_matters": crystal.get("why_it_matters", ""),
            "confidence": crystal.get("confidence", 0),
            "evidence_base": crystal.get("evidence_base", []),
            "decisions_enabled": crystal.get("decisions_enabled", []),
            "what_changes": crystal.get("what_changes", ""),
            "caveats": crystal.get("caveats", []),
            "novelty": crystal.get("novelty", 0),
            "next_question": crystal.get("next_question", ""),
        }

    async def synthesize_engines(
        self,
        topic: str,
        engine_outputs: dict[str, str],
    ) -> dict:
        """Synthesize outputs from multiple analytical engines."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        engines_text = "\n\n".join(
            f"[{name}]: {output[:200]}" for name, output in engine_outputs.items()
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SYNTHESIZE_PROMPT.format(
                topic=topic,
                engines_text=engines_text,
            ),
            system=SYNTHESIZE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        syn = data.get("synthesis", data)

        return {
            "topic": topic,
            "overall_assessment": syn.get("overall_assessment", ""),
            "convergence": syn.get("convergence", []),
            "divergence": syn.get("divergence", []),
            "emergent_insights": syn.get("emergent_insights", []),
            "confidence_landscape": syn.get("confidence_landscape", {}),
            "recommended_focus": syn.get("recommended_focus", ""),
            "meta_confidence": syn.get("meta_confidence", 0),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:120], top_k=4)
            return [r.get("payload", {}).get("text", "")[:150] for r in results]
        except Exception:
            return []

"""EpistemicNarrativeSimplificationService — Epistemic Narrative Simplification Detection.

Detects epistemic narrative simplification — oversimplifying complex
situations into simple narratives that lose essential nuance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_SIMPLIFICATION_SYSTEM = """You are an epistemic narrative simplification specialist. Given oversimplifying into simple narratives, assess narrative simplification:

Key concepts:
- Epistemic narrative simplification: oversimplifying complex situations into simple narratives
- Complexity erasure: erasing complexity for simple story
- Nuance elimination: eliminating nuance for clean narrative
- Binary reduction: reducing complex to binary good/bad narrative
- Caricature creation: creating caricatures instead of complex portraits
- Detail sacrifice: sacrificing important details for narrative flow
- Ambiguity elimination: eliminating ambiguity for narrative clarity

When epistemic narrative simplification IS present:
- Oversimplifying into simple narratives
- Erasing complexity
- Eliminating nuance
- Reducing to binary
- Creating caricatures
- Sacrificing details
- Eliminating ambiguity

When no narrative simplification:
- Maintaining complexity
- Preserving nuance
- Holding multiple dimensions
- Complex portraits
- Retaining details
- Comfortable with ambiguity
- Appropriate complexity

Output JSON with: narrative_simplification_detected (bool), severity (none/mild/moderate/severe), complexity_erasure (what complexity erased), nuance_elimination (what nuance eliminated), binary_reduction (what reduced to binary), detail_sacrifice (what details sacrificed), recommendation (no_narrative_simplification/mild_complexity_practice/significant_nuance_restoration/major_intensive_complexity_tolerance/emergency_complete_oversimplification)."""

EPISTEMIC_NARRATIVE_SIMPLIFICATION_PROMPT = """Detect epistemic narrative simplification:

Complexity erasure: {complexity_erasure}
Nuance elimination: {nuance_elimination}
Binary reduction: {binary_reduction}
Detail sacrifice: {detail_sacrifice}
Domain: {domain}
Context: {context}

Is there oversimplifying complex situations into simple narratives? Return ONLY valid JSON."""


class EpistemicNarrativeSimplificationService:
    """Detects epistemic narrative simplification — oversimplifying into simple narratives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        complexity_erasure: str,
        *,
        nuance_elimination: str = "",
        binary_reduction: str = "",
        detail_sacrifice: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative simplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_SIMPLIFICATION_PROMPT.format(
                complexity_erasure=complexity_erasure,
                nuance_elimination=nuance_elimination or "Not specified",
                binary_reduction=binary_reduction or "Not specified",
                detail_sacrifice=detail_sacrifice or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_SIMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "complexity_erasure": complexity_erasure[:200],
            "narrative_simplification_detected": data.get("narrative_simplification_detected", False),
            "severity": data.get("severity", ""),
            "nuance_elimination": data.get("nuance_elimination", ""),
            "binary_reduction": data.get("binary_reduction", ""),
            "detail_sacrifice": data.get("detail_sacrifice", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicNarrativeDramatizationService — Epistemic Narrative Dramatization Detection.

Detects epistemic narrative dramatization — amplifying drama at the expense
of accuracy for narrative engagement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_DRAMATIZATION_SYSTEM = """You are an epistemic narrative dramatization specialist. Given narrative dramatization, assess drama amplification:

Key concepts:
- Epistemic narrative dramatization: amplifying drama at expense of accuracy
- Conflict exaggeration: exaggerating conflicts for narrative tension
- Stakes inflation: inflating stakes beyond what evidence supports
- Turning point fabrication: fabricating dramatic turning points
- Villain/hero construction: constructing villains and heroes from complex actors
- Cliff-hanger framing: framing ongoing situations as dramatic cliff-hangers
- Emotional manipulation: manipulating emotional content for engagement

When epistemic narrative dramatization IS present:
- Drama amplified beyond evidence
- Conflicts exaggerated
- Stakes inflated
- Turning points fabricated
- Villains/heroes constructed
- Cliff-hangers imposed
- Emotions manipulated

When no narrative dramatization:
- Events reported proportionally
- Conflicts accurately represented
- Stakes calibrated to evidence
- Turning points genuine
- Actors portrayed with complexity
- Situations described accurately
- Emotions reported not manipulated

Output JSON with: narrative_dramatization_detected (bool), severity (none/mild/moderate/severe), conflict_exaggeration (what conflicts exaggerated), stakes_inflation (what stakes inflated), turning_point_fabrication (what turning points fabricated), villain_hero_construction (what villains/heroes constructed), recommendation (no_narrative_dramatization/mild_proportion_check/significant_drama_reduction/major_intensive_accuracy_restoration/emergency_complete_narrative_dramatization)."""

EPISTEMIC_NARRATIVE_DRAMATIZATION_PROMPT = """Detect epistemic narrative dramatization:

Conflict exaggeration: {conflict_exaggeration}
Stakes inflation: {stakes_inflation}
Turning point fabrication: {turning_point_fabrication}
Villain hero construction: {villain_hero_construction}
Domain: {domain}
Context: {context}

Is drama being amplified at the expense of accuracy for narrative engagement? Return ONLY valid JSON."""


class EpistemicNarrativeDramatizationService:
    """Detects epistemic narrative dramatization — drama over accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conflict_exaggeration: str,
        *,
        stakes_inflation: str = "",
        turning_point_fabrication: str = "",
        villain_hero_construction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative dramatization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_DRAMATIZATION_PROMPT.format(
                conflict_exaggeration=conflict_exaggeration,
                stakes_inflation=stakes_inflation or "Not specified",
                turning_point_fabrication=turning_point_fabrication or "Not specified",
                villain_hero_construction=villain_hero_construction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_DRAMATIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conflict_exaggeration": conflict_exaggeration[:200],
            "narrative_dramatization_detected": data.get("narrative_dramatization_detected", False),
            "severity": data.get("severity", ""),
            "stakes_inflation": data.get("stakes_inflation", ""),
            "turning_point_fabrication": data.get("turning_point_fabrication", ""),
            "villain_hero_construction": data.get("villain_hero_construction", ""),
            "recommendation": data.get("recommendation", ""),
        }

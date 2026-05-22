"""EpistemicCompromiseFormationService — Epistemic Compromise Formation Detection.

Detects epistemic compromise formation — forming compromises between
conflicting intellectual needs that partially satisfy each but fully satisfy none.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPROMISE_FORMATION_SYSTEM = """You are an epistemic compromise formation specialist. Given conflicting intellectual needs, assess compromise formation:

Key concepts:
- Epistemic compromise formation: partial satisfaction of conflicting needs
- Symptom as compromise: intellectual symptom serving multiple masters
- Wish and defense: simultaneously expressing and blocking
- Disguised satisfaction: getting need met in unrecognizable form
- Multiple function: single behavior serving contradictory purposes
- Partial gratification: neither need fully met
- Dynamic equilibrium: unstable balance between forces

When epistemic compromise formation IS present:
- Partial satisfaction of conflicting needs
- Symptom serving multiple masters
- Simultaneously expressing and blocking
- Need met in unrecognizable form
- Single behavior serving contradictions
- Neither need fully met
- Unstable balance

When no compromise formation:
- Direct need satisfaction
- Clear symptom function
- Expressing or blocking clearly
- Recognizable need meeting
- Clear behavior purpose
- Needs fully addressed
- Stable resolution

Output JSON with: compromise_formation_detected (bool), severity (none/mild/moderate/severe), conflicting_needs (what opposing), symptom_function (what serving), disguised_satisfaction (what hidden), dynamic_equilibrium (what balancing), recommendation (no_compromise_formation/mild_need_clarification/significant_conflict_resolution/major_intensive_integration/emergency_severe_conflict)."""

EPISTEMIC_COMPROMISE_FORMATION_PROMPT = """Detect epistemic compromise formation:

Conflicting needs: {conflicting_needs}
Symptom function: {symptom_function}
Disguised satisfaction: {disguised_satisfaction}
Dynamic equilibrium: {dynamic_equilibrium}
Domain: {domain}
Context: {context}

Is there compromise between conflicting intellectual needs partially satisfying each? Return ONLY valid JSON."""


class EpistemicCompromiseFormationService:
    """Detects epistemic compromise formation — conflicting needs partially satisfied."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conflicting_needs: str,
        *,
        symptom_function: str = "",
        disguised_satisfaction: str = "",
        dynamic_equilibrium: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic compromise formation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPROMISE_FORMATION_PROMPT.format(
                conflicting_needs=conflicting_needs,
                symptom_function=symptom_function or "Not specified",
                disguised_satisfaction=disguised_satisfaction or "Not specified",
                dynamic_equilibrium=dynamic_equilibrium or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPROMISE_FORMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conflicting_needs": conflicting_needs[:200],
            "compromise_formation_detected": data.get("compromise_formation_detected", False),
            "severity": data.get("severity", ""),
            "symptom_function": data.get("symptom_function", ""),
            "disguised_satisfaction": data.get("disguised_satisfaction", ""),
            "dynamic_equilibrium": data.get("dynamic_equilibrium", ""),
            "recommendation": data.get("recommendation", ""),
        }

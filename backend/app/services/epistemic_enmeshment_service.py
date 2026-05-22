"""EpistemicEnmeshmentService — Epistemic Enmeshment Detection.

Detects epistemic enmeshment — intellectual boundaries so blurred that
individual thinking becomes indistinguishable from group thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENMESHMENT_SYSTEM = """You are an epistemic enmeshment specialist. Given blurred intellectual boundaries, assess enmeshment:

Key concepts:
- Epistemic enmeshment: boundaries so blurred individual thinking lost
- Fusion: cannot distinguish own thoughts from group's
- Differentiation failure: unable to hold separate position
- Loyalty demands: must think alike to belong
- Individuation suppression: punished for independent thought
- Emotional reasoning contagion: group feelings become beliefs
- Exit impossibility: cannot leave without identity collapse

When epistemic enmeshment IS present:
- Boundaries blurred
- Cannot distinguish own thoughts
- Unable to hold separate position
- Must think alike to belong
- Punished for independence
- Group feelings become beliefs
- Cannot leave without collapse

When no enmeshment:
- Clear boundaries
- Own thoughts distinct
- Can hold separate position
- Belonging without conformity
- Independence valued
- Feelings and beliefs separate
- Free to leave

Output JSON with: enmeshment_detected (bool), severity (none/mild/moderate/severe), fusion_level (what indistinguishable), differentiation_failure (what cannot separate), loyalty_demand (what conformity required), individuation_suppression (what punishment), recommendation (no_enmeshment/mild_differentiation_work/significant_boundary_therapy/major_intensive_individuation/emergency_complete_fusion)."""

EPISTEMIC_ENMESHMENT_PROMPT = """Detect epistemic enmeshment:

Fusion level: {fusion_level}
Differentiation failure: {differentiation_failure}
Loyalty demand: {loyalty_demand}
Individuation suppression: {individuation_suppression}
Domain: {domain}
Context: {context}

Are intellectual boundaries so blurred that individual thinking is indistinguishable from group? Return ONLY valid JSON."""


class EpistemicEnmeshmentService:
    """Detects epistemic enmeshment — blurred intellectual boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fusion_level: str,
        *,
        differentiation_failure: str = "",
        loyalty_demand: str = "",
        individuation_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic enmeshment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENMESHMENT_PROMPT.format(
                fusion_level=fusion_level,
                differentiation_failure=differentiation_failure or "Not specified",
                loyalty_demand=loyalty_demand or "Not specified",
                individuation_suppression=individuation_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENMESHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fusion_level": fusion_level[:200],
            "enmeshment_detected": data.get("enmeshment_detected", False),
            "severity": data.get("severity", ""),
            "differentiation_failure": data.get("differentiation_failure", ""),
            "loyalty_demand": data.get("loyalty_demand", ""),
            "individuation_suppression": data.get("individuation_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }

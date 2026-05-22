"""EpistemicExpertiseAlienationService — Epistemic Expertise Alienation Detection.

Detects epistemic expertise alienation — alienation caused by deep
expertise that separates one from non-expert communities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_ALIENATION_SYSTEM = """You are an epistemic expertise alienation specialist. Given alienation from deep expertise, assess expertise alienation:

Key concepts:
- Epistemic expertise alienation: alienation from deep expertise
- Professional isolation: expertise creating distance from others
- Jargon barrier: specialized language excluding connection
- Perspective divergence: expertise changing how one sees everything
- Social cost: expertise making social interaction difficult
- Identity narrowing: becoming defined only by expertise
- Relational sacrifice: relationships lost to expertise demands

When epistemic expertise alienation IS present:
- Alienation from deep expertise
- Expertise creating distance
- Specialized language excluding
- Expertise changing perspective
- Expertise making social interaction difficult
- Becoming defined only by expertise
- Relationships lost to expertise

When no expertise alienation:
- Expertise enriching connections
- Expertise bridging to others
- Language adapting to context
- Perspective broadening
- Expertise enhancing social life
- Multifaceted identity
- Relationships supported by expertise

Output JSON with: expertise_alienation_detected (bool), severity (none/mild/moderate/severe), professional_isolation (what creating distance), jargon_barrier (what excluding), perspective_divergence (what changing), social_cost (what making difficult), recommendation (no_expertise_alienation/mild_bridge_building/significant_integration_work/major_intensive_belonging_therapy/emergency_severe_alienation)."""

EPISTEMIC_EXPERTISE_ALIENATION_PROMPT = """Detect epistemic expertise alienation:

Professional isolation: {professional_isolation}
Jargon barrier: {jargon_barrier}
Perspective divergence: {perspective_divergence}
Social cost: {social_cost}
Domain: {domain}
Context: {context}

Is there alienation caused by deep expertise? Return ONLY valid JSON."""


class EpistemicExpertiseAlienationService:
    """Detects epistemic expertise alienation — alienation from deep expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        professional_isolation: str,
        *,
        jargon_barrier: str = "",
        perspective_divergence: str = "",
        social_cost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise alienation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_ALIENATION_PROMPT.format(
                professional_isolation=professional_isolation,
                jargon_barrier=jargon_barrier or "Not specified",
                perspective_divergence=perspective_divergence or "Not specified",
                social_cost=social_cost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_ALIENATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "professional_isolation": professional_isolation[:200],
            "expertise_alienation_detected": data.get("expertise_alienation_detected", False),
            "severity": data.get("severity", ""),
            "jargon_barrier": data.get("jargon_barrier", ""),
            "perspective_divergence": data.get("perspective_divergence", ""),
            "social_cost": data.get("social_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }

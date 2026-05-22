"""EpistemicCondescensionService — Epistemic Condescension Detection.

Detects epistemic condescension — patronizing engagement with others'
ideas that undermines their intellectual agency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONDESCENSION_SYSTEM = """You are an epistemic condescension specialist. Given patronizing intellectual engagement, assess condescension:

Key concepts:
- Epistemic condescension: patronizing engagement with others' ideas
- Intellectual patronizing: treating others as needing simplification
- Assumed ignorance: presuming others don't understand
- Explanatory excess: over-explaining to signal superiority
- Praise as diminishment: complimenting in ways that belittle
- Infantilization: treating adult thinkers as children
- Benevolent superiority: being kind from a position above

When epistemic condescension IS present:
- Patronizing engagement
- Treating as needing simplification
- Presuming don't understand
- Over-explaining to signal superiority
- Complimenting to belittle
- Treating as children
- Being kind from above

When no condescension:
- Respectful engagement
- Meeting at level
- Checking understanding
- Explaining appropriately
- Genuine compliments
- Treating as adults
- Being kind as equals

Output JSON with: condescension_detected (bool), severity (none/mild/moderate/severe), intellectual_patronizing (what treating as needing simplification), assumed_ignorance (what presuming don't understand), explanatory_excess (what over-explaining), praise_as_diminishment (what complimenting to belittle), recommendation (no_condescension/mild_respect_practice/significant_equality_work/major_intensive_humility_therapy/emergency_active_infantilization)."""

EPISTEMIC_CONDESCENSION_PROMPT = """Detect epistemic condescension:

Intellectual patronizing: {intellectual_patronizing}
Assumed ignorance: {assumed_ignorance}
Explanatory excess: {explanatory_excess}
Praise as diminishment: {praise_as_diminishment}
Domain: {domain}
Context: {context}

Is there patronizing engagement undermining intellectual agency? Return ONLY valid JSON."""


class EpistemicCondescensionService:
    """Detects epistemic condescension — patronizing engagement with others' ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intellectual_patronizing: str,
        *,
        assumed_ignorance: str = "",
        explanatory_excess: str = "",
        praise_as_diminishment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic condescension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONDESCENSION_PROMPT.format(
                intellectual_patronizing=intellectual_patronizing,
                assumed_ignorance=assumed_ignorance or "Not specified",
                explanatory_excess=explanatory_excess or "Not specified",
                praise_as_diminishment=praise_as_diminishment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONDESCENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intellectual_patronizing": intellectual_patronizing[:200],
            "condescension_detected": data.get("condescension_detected", False),
            "severity": data.get("severity", ""),
            "assumed_ignorance": data.get("assumed_ignorance", ""),
            "explanatory_excess": data.get("explanatory_excess", ""),
            "praise_as_diminishment": data.get("praise_as_diminishment", ""),
            "recommendation": data.get("recommendation", ""),
        }

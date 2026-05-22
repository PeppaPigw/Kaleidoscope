"""EpistemicSocialExclusionFearService — Epistemic Social Exclusion Fear Detection.

Detects epistemic social exclusion fear — fear of being excluded from
groups distorting beliefs and intellectual positions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_EXCLUSION_FEAR_SYSTEM = """You are an epistemic social exclusion fear specialist. Given fear of exclusion distorting beliefs, assess social exclusion fear:

Key concepts:
- Epistemic social exclusion fear: fear of exclusion distorting beliefs
- Ostracism avoidance: avoiding beliefs that might lead to ostracism
- Belonging threat: beliefs threatened by need to belong
- Exile anxiety: anxiety about intellectual exile
- Tribe loyalty: loyalty to intellectual tribe overriding truth
- Heresy fear: fear of being seen as heretical
- Outcast prevention: preventing outcast status by belief conformity

When epistemic social exclusion fear IS present:
- Fear of exclusion distorting beliefs
- Avoiding ostracism-risking beliefs
- Belonging threatening beliefs
- Exile anxiety active
- Tribe loyalty overriding truth
- Heresy feared
- Outcast prevention active

When no social exclusion fear:
- Beliefs independent of exclusion fear
- Willing to risk ostracism for truth
- Belonging not threatening beliefs
- No exile anxiety
- Truth overriding tribe loyalty
- Heresy not feared
- Outcast status accepted if necessary

Output JSON with: social_exclusion_fear_detected (bool), severity (none/mild/moderate/severe), ostracism_avoidance (what beliefs avoided to prevent ostracism), belonging_threat (what beliefs threatened by belonging need), tribe_loyalty (what tribe loyalty overriding), heresy_fear (what feared as heretical), recommendation (no_social_exclusion_fear/mild_courage_practice/significant_independence_recovery/major_intensive_autonomy_building/emergency_complete_social_exclusion_fear)."""

EPISTEMIC_SOCIAL_EXCLUSION_FEAR_PROMPT = """Detect epistemic social exclusion fear:

Ostracism avoidance: {ostracism_avoidance}
Belonging threat: {belonging_threat}
Tribe loyalty: {tribe_loyalty}
Heresy fear: {heresy_fear}
Domain: {domain}
Context: {context}

Is fear of exclusion distorting beliefs? Return ONLY valid JSON."""


class EpistemicSocialExclusionFearService:
    """Detects epistemic social exclusion fear — fear of exclusion distorting beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ostracism_avoidance: str,
        *,
        belonging_threat: str = "",
        tribe_loyalty: str = "",
        heresy_fear: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social exclusion fear."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_EXCLUSION_FEAR_PROMPT.format(
                ostracism_avoidance=ostracism_avoidance,
                belonging_threat=belonging_threat or "Not specified",
                tribe_loyalty=tribe_loyalty or "Not specified",
                heresy_fear=heresy_fear or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_EXCLUSION_FEAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ostracism_avoidance": ostracism_avoidance[:200],
            "social_exclusion_fear_detected": data.get("social_exclusion_fear_detected", False),
            "severity": data.get("severity", ""),
            "belonging_threat": data.get("belonging_threat", ""),
            "tribe_loyalty": data.get("tribe_loyalty", ""),
            "heresy_fear": data.get("heresy_fear", ""),
            "recommendation": data.get("recommendation", ""),
        }

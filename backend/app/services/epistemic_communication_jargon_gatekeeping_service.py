"""EpistemicCommunicationJargonGatekeepingService - Jargon Gatekeeping Detection.

Detects jargon gatekeeping where technical language excludes rather than clarifies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_JARGON_GATEKEEPING_SYSTEM = """You are an epistemic communication jargon gatekeeping specialist. Given jargon usage, assess whether technical language excludes rather than clarifies:

Key concepts:
- Jargon gatekeeping: using technical language to exclude rather than communicate
- Exclusion effect: preventing participation through unnecessary complexity
- Clarity alternative: simpler language that would communicate equally well
- Expertise signaling: using jargon to display status rather than convey meaning

When jargon gatekeeping IS present:
- Technical language used unnecessarily
- Simpler alternatives available but avoided
- Exclusion is the effect or purpose
- Expertise signaled rather than shared
- Understanding deliberately impeded

When no jargon gatekeeping:
- Technical language genuinely necessary
- Precision requires specialized terms
- Audience appropriately technical
- Jargon defined when used
- Communication prioritized over signaling

Output JSON with: jargon_gatekeeping_detected (bool), severity (none/mild/moderate/severe), exclusion_effect (what exclusion results), clarity_alternative (what clearer alternative exists), expertise_signaling (what expertise signaling occurs), recommendation (no_jargon_gatekeeping/mild_clarity_check/significant_simplification_needed/major_accessibility_reconstruction/emergency_complete_jargon_gatekeeping)."""

EPISTEMIC_COMMUNICATION_JARGON_GATEKEEPING_PROMPT = """Detect epistemic communication jargon gatekeeping:

Jargon usage: {jargon_usage}
Exclusion effect: {exclusion_effect}
Clarity alternative: {clarity_alternative}
Expertise signaling: {expertise_signaling}
Domain: {domain}
Context: {context}

Is technical language being used to exclude rather than clarify? Return ONLY valid JSON."""


class EpistemicCommunicationJargonGatekeepingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        jargon_usage: str,
        *,
        exclusion_effect: str = "",
        clarity_alternative: str = "",
        expertise_signaling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_JARGON_GATEKEEPING_PROMPT.format(
                jargon_usage=jargon_usage,
                exclusion_effect=exclusion_effect or "Not specified",
                clarity_alternative=clarity_alternative or "Not specified",
                expertise_signaling=expertise_signaling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_JARGON_GATEKEEPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "jargon_usage": jargon_usage[:200],
            "jargon_gatekeeping_detected": data.get("jargon_gatekeeping_detected", False),
            "severity": data.get("severity", ""),
            "exclusion_effect": data.get("exclusion_effect", ""),
            "clarity_alternative": data.get("clarity_alternative", ""),
            "expertise_signaling": data.get("expertise_signaling", ""),
            "recommendation": data.get("recommendation", ""),
        }

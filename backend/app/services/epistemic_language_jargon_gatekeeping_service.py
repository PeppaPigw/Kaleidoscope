"""EpistemicLanguageJargonGatekeepingService - Epistemic Language Jargon Gatekeeping Detection.

Detects epistemic language jargon gatekeeping - jargon used to exclude
non-experts and perform expertise rather than clarify meaning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_JARGON_GATEKEEPING_SYSTEM = """You are an epistemic language jargon gatekeeping specialist. Given jargon that excludes non-experts, assess jargon gatekeeping:

Key concepts:
- Epistemic language jargon gatekeeping: technical language used to exclude rather than clarify
- Exclusionary terminology: terms that block non-experts from participating
- Complexity signaling: complexity used to signal status instead of precision
- Accessibility barrier: language preventing legitimate understanding
- Expertise performance: performing expertise through vocabulary
- Translation refusal: refusing plain-language equivalents
- Participation filtering: language selecting who can speak

When jargon gatekeeping IS present:
- Exclusionary terminology used
- Complexity signals status
- Accessibility barriers raised
- Expertise performed
- Plain translation resisted
- Non-experts excluded
- Participation filtered by vocabulary

When no jargon gatekeeping:
- Technical terms clarify
- Complexity justified by precision
- Accessibility supported
- Expertise explains rather than excludes
- Plain-language translation available
- Non-experts can follow
- Participation remains open

Output JSON with: jargon_gatekeeping_detected (bool), severity (none/mild/moderate/severe), exclusionary_terminology (what terminology excludes), complexity_signaling (what complexity signals), accessibility_barrier (what barrier created), expertise_performance (what expertise performed), recommendation (no_jargon_gatekeeping/mild_plain_language_support/significant_accessibility_rewrite/major_intensive_translation/emergency_complete_jargon_gatekeeping)."""

EPISTEMIC_LANGUAGE_JARGON_GATEKEEPING_PROMPT = """Detect epistemic language jargon gatekeeping:

Exclusionary terminology: {exclusionary_terminology}
Complexity signaling: {complexity_signaling}
Accessibility barrier: {accessibility_barrier}
Expertise performance: {expertise_performance}
Domain: {domain}
Context: {context}

Is jargon being used as epistemic gatekeeping? Return ONLY valid JSON."""


class EpistemicLanguageJargonGatekeepingService:
    """Detects epistemic language jargon gatekeeping - exclusion through terminology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exclusionary_terminology: str,
        *,
        complexity_signaling: str = "",
        accessibility_barrier: str = "",
        expertise_performance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language jargon gatekeeping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_JARGON_GATEKEEPING_PROMPT.format(
                exclusionary_terminology=exclusionary_terminology,
                complexity_signaling=complexity_signaling or "Not specified",
                accessibility_barrier=accessibility_barrier or "Not specified",
                expertise_performance=expertise_performance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_JARGON_GATEKEEPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exclusionary_terminology": exclusionary_terminology[:200],
            "jargon_gatekeeping_detected": data.get("jargon_gatekeeping_detected", False),
            "severity": data.get("severity", ""),
            "complexity_signaling": data.get("complexity_signaling", ""),
            "accessibility_barrier": data.get("accessibility_barrier", ""),
            "expertise_performance": data.get("expertise_performance", ""),
            "recommendation": data.get("recommendation", ""),
        }

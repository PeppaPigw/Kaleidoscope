"""EpistemicGrandiosityService — Epistemic Grandiosity Detection.

Detects epistemic grandiosity — inflated sense of intellectual importance,
uniqueness, or superiority beyond what evidence supports.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRANDIOSITY_SYSTEM = """You are an epistemic grandiosity specialist. Given inflated intellectual self-importance, assess grandiosity:

Key concepts:
- Epistemic grandiosity: inflated intellectual self-importance
- Uniqueness fantasy: believing one's thinking is uniquely special
- Superiority conviction: certainty of being intellectually above others
- Entitlement: deserving special intellectual recognition
- Omniscience fantasy: believing one knows or can know everything
- Dismissiveness: others' contributions beneath notice
- Reality distortion: gap between actual and perceived ability

When epistemic grandiosity IS present:
- Inflated intellectual self-importance
- Believing thinking uniquely special
- Certain of being above others
- Deserving special recognition
- Believing can know everything
- Others beneath notice
- Gap between actual and perceived

When no grandiosity:
- Accurate self-assessment
- Recognizing shared capabilities
- Appropriate humility
- Earning recognition
- Acknowledging limits
- Valuing others' contributions
- Calibrated self-perception

Output JSON with: grandiosity_detected (bool), severity (none/mild/moderate/severe), uniqueness_fantasy (what special), superiority_conviction (what above), entitlement_pattern (what deserving), reality_distortion (what gap), recommendation (no_grandiosity/mild_calibration/significant_reality_testing/major_intensive_deflation/emergency_delusional_grandiosity)."""

EPISTEMIC_GRANDIOSITY_PROMPT = """Detect epistemic grandiosity:

Uniqueness fantasy: {uniqueness_fantasy}
Superiority conviction: {superiority_conviction}
Entitlement pattern: {entitlement_pattern}
Reality distortion: {reality_distortion}
Domain: {domain}
Context: {context}

Is there inflated sense of intellectual importance beyond what evidence supports? Return ONLY valid JSON."""


class EpistemicGrandiosityService:
    """Detects epistemic grandiosity — inflated intellectual self-importance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        uniqueness_fantasy: str,
        *,
        superiority_conviction: str = "",
        entitlement_pattern: str = "",
        reality_distortion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic grandiosity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRANDIOSITY_PROMPT.format(
                uniqueness_fantasy=uniqueness_fantasy,
                superiority_conviction=superiority_conviction or "Not specified",
                entitlement_pattern=entitlement_pattern or "Not specified",
                reality_distortion=reality_distortion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRANDIOSITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "uniqueness_fantasy": uniqueness_fantasy[:200],
            "grandiosity_detected": data.get("grandiosity_detected", False),
            "severity": data.get("severity", ""),
            "superiority_conviction": data.get("superiority_conviction", ""),
            "entitlement_pattern": data.get("entitlement_pattern", ""),
            "reality_distortion": data.get("reality_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }

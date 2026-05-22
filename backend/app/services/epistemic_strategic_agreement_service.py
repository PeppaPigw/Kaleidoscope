"""EpistemicStrategicAgreementService — Epistemic Strategic Agreement Detection.

Detects epistemic strategic agreement — agreeing strategically rather
than from genuine conviction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRATEGIC_AGREEMENT_SYSTEM = """You are an epistemic strategic agreement specialist. Given agreeing strategically not from conviction, assess strategic agreement:

Key concepts:
- Epistemic strategic agreement: agreeing strategically not from conviction
- Expedient consensus: agreeing to avoid conflict not from belief
- Power-based agreement: agreeing with powerful people regardless of truth
- Social lubrication: agreement as social tool not intellectual position
- Conflict avoidance: agreeing to prevent confrontation
- Career-protective agreement: agreeing to protect professional standing
- Anticipatory compliance: agreeing before even being asked

When epistemic strategic agreement IS present:
- Agreeing strategically not from conviction
- Agreeing to avoid conflict
- Agreeing with powerful regardless of truth
- Agreement as social tool
- Agreeing to prevent confrontation
- Agreeing to protect standing
- Agreeing before being asked

When no strategic agreement:
- Genuine agreement
- Honest disagreement when warranted
- Truth over power
- Authentic intellectual positions
- Comfortable with confrontation
- Integrity over career
- Independent judgment

Output JSON with: strategic_agreement_detected (bool), severity (none/mild/moderate/severe), expedient_consensus (what agreeing to avoid conflict), power_based_agreement (what agreeing with powerful), conflict_avoidance (what preventing confrontation about), career_protective (what protecting standing about), recommendation (no_strategic_agreement/mild_honesty_practice/significant_courage_building/major_intensive_integrity_work/emergency_complete_intellectual_capitulation)."""

EPISTEMIC_STRATEGIC_AGREEMENT_PROMPT = """Detect epistemic strategic agreement:

Expedient consensus: {expedient_consensus}
Power based agreement: {power_based_agreement}
Conflict avoidance: {conflict_avoidance}
Career protective: {career_protective}
Domain: {domain}
Context: {context}

Is there agreeing strategically rather than from genuine conviction? Return ONLY valid JSON."""


class EpistemicStrategicAgreementService:
    """Detects epistemic strategic agreement — agreeing strategically not from conviction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        expedient_consensus: str,
        *,
        power_based_agreement: str = "",
        conflict_avoidance: str = "",
        career_protective: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic strategic agreement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRATEGIC_AGREEMENT_PROMPT.format(
                expedient_consensus=expedient_consensus,
                power_based_agreement=power_based_agreement or "Not specified",
                conflict_avoidance=conflict_avoidance or "Not specified",
                career_protective=career_protective or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRATEGIC_AGREEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "expedient_consensus": expedient_consensus[:200],
            "strategic_agreement_detected": data.get("strategic_agreement_detected", False),
            "severity": data.get("severity", ""),
            "power_based_agreement": data.get("power_based_agreement", ""),
            "conflict_avoidance": data.get("conflict_avoidance", ""),
            "career_protective": data.get("career_protective", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicCommunicationStrategicAmbiguityService - Strategic Ambiguity Detection.

Detects strategic ambiguity where deliberate vagueness avoids commitment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_STRATEGIC_AMBIGUITY_SYSTEM = """You are an epistemic communication strategic ambiguity specialist. Given an ambiguous claim, assess whether deliberate vagueness avoids commitment:

Key concepts:
- Strategic ambiguity: deliberate vagueness to maintain interpretive flexibility
- Commitment avoidance: refusing to take clear positions
- Interpretive flexibility: allowing multiple readings to avoid accountability
- Accountability escape: using vagueness to deny specific meanings later

When strategic ambiguity IS present:
- Claims deliberately vague
- Commitment systematically avoided
- Multiple interpretations maintained
- Accountability escaped through ambiguity
- Plausible deniability preserved

When no strategic ambiguity:
- Claims appropriately precise
- Positions clearly stated
- Meaning unambiguous
- Accountability accepted
- Vagueness reflects genuine uncertainty

Output JSON with: strategic_ambiguity_detected (bool), severity (none/mild/moderate/severe), commitment_avoidance (what commitment avoided), interpretive_flexibility (what flexibility maintained), accountability_escape (what accountability escaped), recommendation (no_strategic_ambiguity/mild_precision_check/significant_commitment_request/major_clarity_reconstruction/emergency_complete_strategic_ambiguity)."""

EPISTEMIC_COMMUNICATION_STRATEGIC_AMBIGUITY_PROMPT = """Detect epistemic communication strategic ambiguity:

Ambiguous claim: {ambiguous_claim}
Commitment avoidance: {commitment_avoidance}
Interpretive flexibility: {interpretive_flexibility}
Accountability escape: {accountability_escape}
Domain: {domain}
Context: {context}

Is deliberate vagueness being used to avoid commitment? Return ONLY valid JSON."""


class EpistemicCommunicationStrategicAmbiguityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ambiguous_claim: str,
        *,
        commitment_avoidance: str = "",
        interpretive_flexibility: str = "",
        accountability_escape: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_STRATEGIC_AMBIGUITY_PROMPT.format(
                ambiguous_claim=ambiguous_claim,
                commitment_avoidance=commitment_avoidance or "Not specified",
                interpretive_flexibility=interpretive_flexibility or "Not specified",
                accountability_escape=accountability_escape or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_STRATEGIC_AMBIGUITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ambiguous_claim": ambiguous_claim[:200],
            "strategic_ambiguity_detected": data.get("strategic_ambiguity_detected", False),
            "severity": data.get("severity", ""),
            "commitment_avoidance": data.get("commitment_avoidance", ""),
            "interpretive_flexibility": data.get("interpretive_flexibility", ""),
            "accountability_escape": data.get("accountability_escape", ""),
            "recommendation": data.get("recommendation", ""),
        }

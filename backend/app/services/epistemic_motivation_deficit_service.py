"""EpistemicMotivationDeficitService — Epistemic Motivation Deficit Detection.

Detects epistemic motivation deficit — lack of motivation degrading
epistemic effort and quality of inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOTIVATION_DEFICIT_SYSTEM = """You are an epistemic motivation deficit specialist. Given lack of motivation degrading epistemic effort, assess motivation deficit:

Key concepts:
- Epistemic motivation deficit: lack of motivation degrading epistemic effort
- Inquiry apathy: not caring enough to investigate properly
- Curiosity death: curiosity extinguished about important topics
- Effort avoidance: avoiding the effort needed for good epistemics
- Intellectual laziness: taking shortcuts due to low motivation
- Engagement withdrawal: withdrawing from intellectual engagement
- Quality indifference: indifferent to quality of understanding

When epistemic motivation deficit IS present:
- Motivation lacking for inquiry
- Apathy toward investigation
- Curiosity extinguished
- Effort being avoided
- Intellectual shortcuts taken
- Engagement withdrawn
- Quality indifferent

When no motivation deficit:
- Motivation adequate for inquiry
- Engaged in investigation
- Curiosity active
- Effort willingly applied
- Intellectual rigor maintained
- Engagement sustained
- Quality valued

Output JSON with: motivation_deficit_detected (bool), severity (none/mild/moderate/severe), inquiry_apathy (what apathetic about investigating), curiosity_death (what curiosity extinguished about), effort_avoidance (what effort being avoided), engagement_withdrawal (what withdrawing from), recommendation (no_motivation_deficit/mild_curiosity_rekindling/significant_engagement_recovery/major_intensive_motivation_restoration/emergency_complete_motivation_deficit)."""

EPISTEMIC_MOTIVATION_DEFICIT_PROMPT = """Detect epistemic motivation deficit:

Inquiry apathy: {inquiry_apathy}
Curiosity death: {curiosity_death}
Effort avoidance: {effort_avoidance}
Engagement withdrawal: {engagement_withdrawal}
Domain: {domain}
Context: {context}

Is lack of motivation degrading epistemic effort? Return ONLY valid JSON."""


class EpistemicMotivationDeficitService:
    """Detects epistemic motivation deficit — lack of motivation degrading effort."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inquiry_apathy: str,
        *,
        curiosity_death: str = "",
        effort_avoidance: str = "",
        engagement_withdrawal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic motivation deficit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOTIVATION_DEFICIT_PROMPT.format(
                inquiry_apathy=inquiry_apathy,
                curiosity_death=curiosity_death or "Not specified",
                effort_avoidance=effort_avoidance or "Not specified",
                engagement_withdrawal=engagement_withdrawal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOTIVATION_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inquiry_apathy": inquiry_apathy[:200],
            "motivation_deficit_detected": data.get("motivation_deficit_detected", False),
            "severity": data.get("severity", ""),
            "curiosity_death": data.get("curiosity_death", ""),
            "effort_avoidance": data.get("effort_avoidance", ""),
            "engagement_withdrawal": data.get("engagement_withdrawal", ""),
            "recommendation": data.get("recommendation", ""),
        }

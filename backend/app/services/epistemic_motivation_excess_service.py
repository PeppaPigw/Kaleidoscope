"""EpistemicMotivationExcessService — Epistemic Motivation Excess Detection.

Detects epistemic motivation excess — excessive motivation creating bias
toward desired conclusions and undermining objectivity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOTIVATION_EXCESS_SYSTEM = """You are an epistemic motivation excess specialist. Given excessive motivation creating bias, assess motivation excess:

Key concepts:
- Epistemic motivation excess: excessive motivation creating bias toward desired conclusions
- Conclusion hunger: desperately wanting a specific conclusion
- Confirmation drive: driven to confirm rather than test
- Outcome attachment: attached to specific epistemic outcomes
- Desire-driven inquiry: inquiry driven by desire not truth
- Wishful investigation: investigating to confirm wishes
- Goal contamination: goals contaminating epistemic process

When epistemic motivation excess IS present:
- Excessive motivation creating bias
- Hungry for specific conclusions
- Driven to confirm
- Attached to outcomes
- Desire driving inquiry
- Investigating wishfully
- Goals contaminating process

When no motivation excess:
- Motivation balanced
- Open to any conclusion
- Testing not confirming
- Detached from outcomes
- Truth driving inquiry
- Investigating objectively
- Goals separate from process

Output JSON with: motivation_excess_detected (bool), severity (none/mild/moderate/severe), conclusion_hunger (what conclusions desperately wanted), confirmation_drive (what driven to confirm), outcome_attachment (what outcomes attached to), goal_contamination (what goals contaminating), recommendation (no_motivation_excess/mild_detachment_practice/significant_objectivity_recovery/major_intensive_neutrality_building/emergency_complete_motivation_excess)."""

EPISTEMIC_MOTIVATION_EXCESS_PROMPT = """Detect epistemic motivation excess:

Conclusion hunger: {conclusion_hunger}
Confirmation drive: {confirmation_drive}
Outcome attachment: {outcome_attachment}
Goal contamination: {goal_contamination}
Domain: {domain}
Context: {context}

Is excessive motivation creating bias toward desired conclusions? Return ONLY valid JSON."""


class EpistemicMotivationExcessService:
    """Detects epistemic motivation excess — excessive motivation creating bias."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion_hunger: str,
        *,
        confirmation_drive: str = "",
        outcome_attachment: str = "",
        goal_contamination: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic motivation excess."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOTIVATION_EXCESS_PROMPT.format(
                conclusion_hunger=conclusion_hunger,
                confirmation_drive=confirmation_drive or "Not specified",
                outcome_attachment=outcome_attachment or "Not specified",
                goal_contamination=goal_contamination or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOTIVATION_EXCESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion_hunger": conclusion_hunger[:200],
            "motivation_excess_detected": data.get("motivation_excess_detected", False),
            "severity": data.get("severity", ""),
            "confirmation_drive": data.get("confirmation_drive", ""),
            "outcome_attachment": data.get("outcome_attachment", ""),
            "goal_contamination": data.get("goal_contamination", ""),
            "recommendation": data.get("recommendation", ""),
        }

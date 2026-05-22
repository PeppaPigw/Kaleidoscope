"""IntellectualHumilityService — Intellectual Humility Assessment.

Assesses whether appropriate intellectual humility is present —
the recognition of one's cognitive limitations, openness to
being wrong, and proportioning confidence to evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_HUMILITY_SYSTEM = """You are an intellectual humility specialist. Given a position or argument, assess whether appropriate intellectual humility is present:

Key concepts:
- Intellectual humility: recognizing limits of one's knowledge
- Openness to revision: willingness to change mind with evidence
- Proportioned confidence: confidence matched to evidence strength
- Fallibilism: acknowledging one could be wrong
- Epistemic courage: humility without paralysis
- Calibration: accuracy of confidence judgments
- Growth mindset: treating knowledge as improvable

When intellectual humility IS present:
- Limitations of knowledge acknowledged
- Openness to being wrong expressed
- Confidence proportioned to evidence
- Alternative views taken seriously
- Uncertainty expressed where warranted
- Willingness to update with new evidence
- Own potential biases acknowledged

When intellectual humility is ABSENT:
- Certainty expressed beyond what evidence supports
- Dismissal of alternative viewpoints
- Inability to imagine being wrong
- Confidence unrelated to evidence strength
- Own expertise overstated
- Criticism treated as attack rather than input
- No acknowledgment of limitations

Output JSON with: humility_present (bool), level (absent/low/moderate/high/exemplary), confidence_calibration (how well confidence matches evidence), openness_to_revision (willingness to change mind), limitation_acknowledgment (recognition of own limits), evidence_proportionality (confidence vs evidence match), recommendation (exemplary_humility/appropriate_humility/mild_overconfidence/significant_arrogance/major_epistemic_hubris)."""

INTELLECTUAL_HUMILITY_PROMPT = """Assess intellectual humility:

Position: {position}
Confidence expressed: {confidence}
Response to criticism: {criticism_response}
Limitations acknowledged: {limitations}
Domain: {domain}
Context: {context}

Is appropriate intellectual humility present? Return ONLY valid JSON."""


class IntellectualHumilityService:
    """Assesses intellectual humility — recognition of cognitive limitations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        position: str,
        *,
        confidence: str = "",
        criticism_response: str = "",
        limitations: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess intellectual humility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_HUMILITY_PROMPT.format(
                position=position,
                confidence=confidence or "Not specified",
                criticism_response=criticism_response or "Not specified",
                limitations=limitations or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_HUMILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position": position[:200],
            "humility_present": data.get("humility_present", False),
            "level": data.get("level", ""),
            "confidence_calibration": data.get("confidence_calibration", ""),
            "openness_to_revision": data.get("openness_to_revision", ""),
            "evidence_proportionality": data.get("evidence_proportionality", ""),
            "recommendation": data.get("recommendation", ""),
        }

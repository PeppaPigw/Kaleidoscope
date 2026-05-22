"""EpistemicReactionFormationService — Epistemic Reaction Formation Detection.

Detects epistemic reaction formation — adopting intellectual positions that
are the exact opposite of one's true beliefs to defend against anxiety.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REACTION_FORMATION_SYSTEM = """You are an epistemic reaction formation specialist. Given opposite-position adoption, assess reaction formation:

Key concepts:
- Epistemic reaction formation: adopting opposite of true beliefs
- Overcompensation: excessive advocacy of opposite position
- Anxiety defense: true belief causes unbearable anxiety
- Rigidity: inflexible adherence to adopted position
- Protest too much: intensity reveals underlying truth
- Unconscious reversal: not aware of the switch
- Brittle conviction: collapses under pressure

When epistemic reaction formation IS present:
- Adopting opposite position
- Excessive advocacy
- True belief causes anxiety
- Inflexible adherence
- Intensity reveals truth
- Unaware of switch
- Collapses under pressure

When no reaction formation:
- Authentic positions
- Proportionate advocacy
- Beliefs don't cause anxiety
- Flexible engagement
- Consistent intensity
- Self-aware
- Robust under pressure

Output JSON with: reaction_formation_detected (bool), severity (none/mild/moderate/severe), overcompensation_pattern (what excessive), anxiety_source (what causing), rigidity_level (what inflexible), brittle_conviction (what collapses), recommendation (no_reaction_formation/mild_authenticity_exploration/significant_anxiety_therapy/major_intensive_integration/emergency_complete_reversal)."""

EPISTEMIC_REACTION_FORMATION_PROMPT = """Detect epistemic reaction formation:

Overcompensation pattern: {overcompensation_pattern}
Anxiety source: {anxiety_source}
Rigidity level: {rigidity_level}
Brittle conviction: {brittle_conviction}
Domain: {domain}
Context: {context}

Is there adoption of intellectual positions opposite to true beliefs to defend against anxiety? Return ONLY valid JSON."""


class EpistemicReactionFormationService:
    """Detects epistemic reaction formation — adopting opposite positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        overcompensation_pattern: str,
        *,
        anxiety_source: str = "",
        rigidity_level: str = "",
        brittle_conviction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reaction formation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REACTION_FORMATION_PROMPT.format(
                overcompensation_pattern=overcompensation_pattern,
                anxiety_source=anxiety_source or "Not specified",
                rigidity_level=rigidity_level or "Not specified",
                brittle_conviction=brittle_conviction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REACTION_FORMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overcompensation_pattern": overcompensation_pattern[:200],
            "reaction_formation_detected": data.get("reaction_formation_detected", False),
            "severity": data.get("severity", ""),
            "anxiety_source": data.get("anxiety_source", ""),
            "rigidity_level": data.get("rigidity_level", ""),
            "brittle_conviction": data.get("brittle_conviction", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicNarrativeJustWorldHypothesisService - Just World Hypothesis Detection.

Detects just world hypothesis where outcomes are assumed to be deserved.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_JUST_WORLD_HYPOTHESIS_SYSTEM = """You are an epistemic narrative just world hypothesis specialist. Given outcome attributions, assess whether outcomes are assumed deserved:

Key concepts:
- Just world hypothesis: believing outcomes are inherently deserved or earned
- Victim blaming: attributing misfortune to victim's character or choices
- Merit mythology: assuming success proves virtue and failure proves vice
- Structural blindness: ignoring systemic factors in outcome distribution

When just world hypothesis IS present:
- Outcomes assumed deserved
- Victims blamed for misfortune
- Success attributed to merit alone
- Structural factors ignored
- Moral universe assumed fair

When no just world hypothesis:
- Outcomes recognized as multiply determined
- Structural factors acknowledged
- Luck and circumstance considered
- Victim experience validated
- Systemic analysis included

Output JSON with: just_world_detected (bool), severity (none/mild/moderate/severe), victim_blaming (what victim blaming), merit_mythology (what merit mythology), structural_blindness (what structural blindness), recommendation (no_just_world/mild_structural_check/significant_systemic_analysis/major_attribution_reconstruction/emergency_complete_just_world)."""

EPISTEMIC_NARRATIVE_JUST_WORLD_HYPOTHESIS_PROMPT = """Detect epistemic narrative just world hypothesis:

Outcome attribution: {outcome_attribution}
Victim blaming: {victim_blaming}
Merit mythology: {merit_mythology}
Structural blindness: {structural_blindness}
Domain: {domain}
Context: {context}

Are outcomes being assumed deserved? Return ONLY valid JSON."""


class EpistemicNarrativeJustWorldHypothesisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outcome_attribution: str,
        *,
        victim_blaming: str = "",
        merit_mythology: str = "",
        structural_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_JUST_WORLD_HYPOTHESIS_PROMPT.format(
                outcome_attribution=outcome_attribution,
                victim_blaming=victim_blaming or "Not specified",
                merit_mythology=merit_mythology or "Not specified",
                structural_blindness=structural_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_JUST_WORLD_HYPOTHESIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outcome_attribution": outcome_attribution[:200],
            "just_world_detected": data.get("just_world_detected", False),
            "severity": data.get("severity", ""),
            "victim_blaming": data.get("victim_blaming", ""),
            "merit_mythology": data.get("merit_mythology", ""),
            "structural_blindness": data.get("structural_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }

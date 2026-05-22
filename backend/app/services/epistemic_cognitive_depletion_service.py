"""EpistemicCognitiveDepletionService — Epistemic Cognitive Depletion Detection.

Detects epistemic cognitive depletion — depleted cognitive resources
degrading epistemic quality and judgment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_DEPLETION_SYSTEM = """You are an epistemic cognitive depletion specialist. Given depleted cognitive resources degrading quality, assess cognitive depletion:

Key concepts:
- Epistemic cognitive depletion: depleted resources degrading epistemic quality
- Willpower exhaustion: exhausted self-control affecting judgment
- Mental fatigue: tired mind making poor epistemic choices
- Ego depletion: depleted self-regulation affecting reasoning
- Cognitive budget spent: used up cognitive resources for the day
- Diminished returns: each additional effort yielding less insight
- Recovery deficit: insufficient recovery between cognitive demands

When epistemic cognitive depletion IS present:
- Resources depleted
- Willpower exhausted
- Mental fatigue affecting judgment
- Self-regulation depleted
- Cognitive budget spent
- Diminishing returns evident
- Recovery insufficient

When no cognitive depletion:
- Resources adequate
- Willpower available
- Mind fresh and clear
- Self-regulation intact
- Cognitive budget available
- Returns still productive
- Recovery sufficient

Output JSON with: cognitive_depletion_detected (bool), severity (none/mild/moderate/severe), willpower_exhaustion (what exhausted about), mental_fatigue (what fatigued about), ego_depletion (what depleted about), recovery_deficit (what recovery lacking), recommendation (no_cognitive_depletion/mild_rest_needed/significant_recovery_required/major_intensive_restoration/emergency_complete_cognitive_depletion)."""

EPISTEMIC_COGNITIVE_DEPLETION_PROMPT = """Detect epistemic cognitive depletion:

Willpower exhaustion: {willpower_exhaustion}
Mental fatigue: {mental_fatigue}
Ego depletion: {ego_depletion}
Recovery deficit: {recovery_deficit}
Domain: {domain}
Context: {context}

Are depleted cognitive resources degrading epistemic quality? Return ONLY valid JSON."""


class EpistemicCognitiveDepletionService:
    """Detects epistemic cognitive depletion — depleted resources degrading quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        willpower_exhaustion: str,
        *,
        mental_fatigue: str = "",
        ego_depletion: str = "",
        recovery_deficit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive depletion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_DEPLETION_PROMPT.format(
                willpower_exhaustion=willpower_exhaustion,
                mental_fatigue=mental_fatigue or "Not specified",
                ego_depletion=ego_depletion or "Not specified",
                recovery_deficit=recovery_deficit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_DEPLETION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "willpower_exhaustion": willpower_exhaustion[:200],
            "cognitive_depletion_detected": data.get("cognitive_depletion_detected", False),
            "severity": data.get("severity", ""),
            "mental_fatigue": data.get("mental_fatigue", ""),
            "ego_depletion": data.get("ego_depletion", ""),
            "recovery_deficit": data.get("recovery_deficit", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMaliciousEnvyService — Epistemic Malicious Envy Detection.

Detects epistemic malicious envy — destructive envy wanting to diminish
or destroy others' intellectual achievements.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MALICIOUS_ENVY_SYSTEM = """You are an epistemic malicious envy specialist. Given destructive intellectual envy, assess malicious envy:

Key concepts:
- Epistemic malicious envy: wanting to diminish others' achievements
- Destructive impulse: desire to tear down intellectual success
- Leveling: wanting to bring others down to own level
- Devaluation: dismissing others' genuine contributions
- Sabotage: actively undermining others' intellectual work
- Bitterness: chronic resentment of others' abilities
- Zero-sum thinking: their success means my failure

When epistemic malicious envy IS present:
- Wanting to diminish achievements
- Desire to tear down
- Wanting to bring down
- Dismissing contributions
- Undermining work
- Chronic resentment
- Their success = my failure

When no malicious envy:
- Celebrating others' success
- Supporting achievement
- Comfortable with difference
- Acknowledging contributions
- Supporting work
- Generous spirit
- Abundance thinking

Output JSON with: malicious_envy_detected (bool), severity (none/mild/moderate/severe), destructive_impulse (what wanting to tear down), leveling_pattern (what bringing down), sabotage_behavior (what undermining), zero_sum_thinking (what their success means), recommendation (no_malicious_envy/mild_envy_awareness/significant_envy_processing/major_intensive_envy_therapy/emergency_destructive_acting_out)."""

EPISTEMIC_MALICIOUS_ENVY_PROMPT = """Detect epistemic malicious envy:

Destructive impulse: {destructive_impulse}
Leveling pattern: {leveling_pattern}
Sabotage behavior: {sabotage_behavior}
Zero sum thinking: {zero_sum_thinking}
Domain: {domain}
Context: {context}

Is there destructive envy wanting to diminish others' intellectual achievements? Return ONLY valid JSON."""


class EpistemicMaliciousEnvyService:
    """Detects epistemic malicious envy — wanting to diminish others' achievements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        destructive_impulse: str,
        *,
        leveling_pattern: str = "",
        sabotage_behavior: str = "",
        zero_sum_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic malicious envy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MALICIOUS_ENVY_PROMPT.format(
                destructive_impulse=destructive_impulse,
                leveling_pattern=leveling_pattern or "Not specified",
                sabotage_behavior=sabotage_behavior or "Not specified",
                zero_sum_thinking=zero_sum_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MALICIOUS_ENVY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "destructive_impulse": destructive_impulse[:200],
            "malicious_envy_detected": data.get("malicious_envy_detected", False),
            "severity": data.get("severity", ""),
            "leveling_pattern": data.get("leveling_pattern", ""),
            "sabotage_behavior": data.get("sabotage_behavior", ""),
            "zero_sum_thinking": data.get("zero_sum_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }

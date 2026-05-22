"""EpistemicEnvyDenialService — Epistemic Envy Denial Detection.

Detects epistemic envy denial — refusing to acknowledge envy while
exhibiting its behavioral signatures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVY_DENIAL_SYSTEM = """You are an epistemic envy denial specialist. Given denied envy with behavioral signatures, assess envy denial:

Key concepts:
- Epistemic envy denial: refusing to acknowledge envy
- Reaction formation: converting envy into exaggerated praise
- Dismissal: claiming not to care about envied achievement
- Rationalization: finding reasons envied thing is flawed
- Displacement: redirecting envy onto safer targets
- Moral superiority: claiming above such feelings
- Behavioral leakage: envy showing despite denial

When epistemic envy denial IS present:
- Refusing to acknowledge envy
- Converting to exaggerated praise
- Claiming not to care
- Finding reasons thing is flawed
- Redirecting onto safer targets
- Claiming above such feelings
- Envy showing despite denial

When no envy denial:
- Acknowledging envy openly
- Genuine praise
- Honest about caring
- Fair assessment
- Direct engagement
- Humble about feelings
- Congruent behavior

Output JSON with: envy_denial_detected (bool), severity (none/mild/moderate/severe), reaction_formation (what converting to praise), dismissal_pattern (what claiming not to care about), rationalization (what finding flawed), behavioral_leakage (what showing despite denial), recommendation (no_envy_denial/mild_awareness_building/significant_envy_acknowledgment/major_intensive_honesty_work/emergency_severe_denial)."""

EPISTEMIC_ENVY_DENIAL_PROMPT = """Detect epistemic envy denial:

Reaction formation: {reaction_formation}
Dismissal pattern: {dismissal_pattern}
Rationalization: {rationalization}
Behavioral leakage: {behavioral_leakage}
Domain: {domain}
Context: {context}

Is there refusing to acknowledge envy while exhibiting its behavioral signatures? Return ONLY valid JSON."""


class EpistemicEnvyDenialService:
    """Detects epistemic envy denial — refusing to acknowledge envy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reaction_formation: str,
        *,
        dismissal_pattern: str = "",
        rationalization: str = "",
        behavioral_leakage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic envy denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVY_DENIAL_PROMPT.format(
                reaction_formation=reaction_formation,
                dismissal_pattern=dismissal_pattern or "Not specified",
                rationalization=rationalization or "Not specified",
                behavioral_leakage=behavioral_leakage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVY_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reaction_formation": reaction_formation[:200],
            "envy_denial_detected": data.get("envy_denial_detected", False),
            "severity": data.get("severity", ""),
            "dismissal_pattern": data.get("dismissal_pattern", ""),
            "rationalization": data.get("rationalization", ""),
            "behavioral_leakage": data.get("behavioral_leakage", ""),
            "recommendation": data.get("recommendation", ""),
        }

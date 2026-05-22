"""DeindividuationService — Deindividuation Detection.

Detects deindividuation — loss of self-awareness and individual
accountability in group settings, leading to behavior that
violates personal norms. Zimbardo (1969). Anonymity + group
membership → reduced self-regulation. People do things in
groups they would never do alone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEINDIVIDUATION_SYSTEM = """You are a deindividuation specialist. Given a group behavior situation, assess whether loss of individual identity is leading to norm-violating behavior:

Key concepts (Zimbardo, 1969):
- Deindividuation: loss of self-awareness in groups
- Anonymity effect: reduced accountability enables norm violation
- Group immersion: individual identity subsumed by group identity
- Reduced self-regulation: weakened internal behavioral controls
- Mob mentality: collective behavior exceeding individual norms
- Online disinhibition: digital anonymity enabling deindividuation
- Uniform effect: shared appearance reducing individual identity

When deindividuation IS present:
- Behavior in groups that individuals would never do alone
- Anonymity enabling actions that violate personal values
- "Everyone else was doing it" as justification
- Online behavior that differs dramatically from in-person
- Group decisions more extreme than any individual would choose
- Loss of personal accountability in collective action
- "I got caught up in the moment"

When group behavior IS appropriate:
- The behavior aligns with individual values
- People would make the same choice individually
- Group membership enhances rather than overrides judgment
- Individual accountability is maintained
- The person can articulate personal reasons for the behavior

Output JSON with: deindividuation_present (bool), severity (none/mild/moderate/severe), situation (what group behavior is occurring), anonymity_level (how anonymous are individuals), norm_violation (what norms are being violated), individual_vs_group (would individuals behave this way alone?), accountability (is individual accountability maintained?), self_awareness (is self-awareness reduced?), recommendation (behavior_appropriate/mild_deindividuation/significant_norm_violation/major_deindividuation/restore_individual_accountability)."""

DEINDIVIDUATION_PROMPT = """Detect deindividuation:

Situation: {situation}
Group dynamics: {dynamics}
Behavior: {behavior}
Anonymity: {anonymity}
Domain: {domain}
Context: {context}

Is loss of individual identity leading to norm-violating behavior? Return ONLY valid JSON."""


class DeindividuationService:
    """Detects deindividuation — loss of self-awareness enabling norm violation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        dynamics: str = "",
        behavior: str = "",
        anonymity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deindividuation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEINDIVIDUATION_PROMPT.format(
                situation=situation,
                dynamics=dynamics or "Not specified",
                behavior=behavior or "Not specified",
                anonymity=anonymity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEINDIVIDUATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "deindividuation_present": data.get("deindividuation_present", False),
            "severity": data.get("severity", ""),
            "anonymity_level": data.get("anonymity_level", ""),
            "norm_violation": data.get("norm_violation", ""),
            "individual_vs_group": data.get("individual_vs_group", ""),
            "accountability": data.get("accountability", ""),
            "self_awareness": data.get("self_awareness", ""),
            "recommendation": data.get("recommendation", ""),
        }

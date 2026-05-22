"""IdentityProtectiveService — Identity-Protective Cognition Detection.

Detects identity-protective cognition — processing information
in ways that protect one's group identity and cultural worldview.
Kahan (2013). People don't just have beliefs — they have
identities built around beliefs. Threatening the belief
threatens the identity, triggering defensive cognition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IDENTITY_PROTECTIVE_SYSTEM = """You are an identity-protective cognition specialist. Given a reasoning situation, assess whether information processing is being distorted to protect group identity:

Key concepts (Kahan, 2013):
- Identity-protective cognition: reasoning to protect group membership
- Cultural cognition: risk perceptions shaped by cultural worldview
- Expressive rationality: beliefs as badges of group membership
- Identity threat: information that challenges group-defining beliefs
- Motivated system 2 reasoning: using analytical thinking defensively
- Tribal epistemology: truth determined by group consensus
- Belief as identity: "I believe X" means "I am the kind of person who believes X"

When identity-protective cognition IS present:
- Rejecting evidence because accepting it would alienate one's group
- "People like us don't believe that"
- Evaluating evidence based on what conclusion serves group identity
- Treating belief change as betrayal of community
- Using sophistication to defend group positions more effectively
- Dismissing experts who challenge group consensus
- Framing factual questions as loyalty tests

When reasoning IS independent:
- Willing to update beliefs even when group disagrees
- Evaluating evidence on merits regardless of identity implications
- Acknowledging when own group's position is weakly supported
- Separating factual questions from identity questions
- Engaging with challenging evidence rather than dismissing sources

Output JSON with: identity_protective_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning is being examined), identity_at_stake (what group identity is threatened), threat (what information threatens the identity), defensive_strategy (how is the identity being protected), group_pressure (what social pressure exists), independence_cost (what would independent thinking cost), recommendation (reasoning_independent/mild_identity_influence/significant_identity_protection/major_tribal_epistemology/separate_identity_from_evidence)."""

IDENTITY_PROTECTIVE_PROMPT = """Detect identity-protective cognition:

Reasoning: {reasoning}
Identity: {identity}
Threat: {threat}
Group context: {group_context}
Domain: {domain}
Context: {context}

Is information processing being distorted to protect group identity? Return ONLY valid JSON."""


class IdentityProtectiveService:
    """Detects identity-protective cognition — reasoning to protect group membership."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        identity: str = "",
        threat: str = "",
        group_context: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect identity-protective cognition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IDENTITY_PROTECTIVE_PROMPT.format(
                reasoning=reasoning,
                identity=identity or "Not specified",
                threat=threat or "Not specified",
                group_context=group_context or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IDENTITY_PROTECTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "identity_protective_present": data.get("identity_protective_present", False),
            "severity": data.get("severity", ""),
            "identity_at_stake": data.get("identity_at_stake", ""),
            "threat": data.get("threat", ""),
            "defensive_strategy": data.get("defensive_strategy", ""),
            "group_pressure": data.get("group_pressure", ""),
            "independence_cost": data.get("independence_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }

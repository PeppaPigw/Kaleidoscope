"""EpistemicEpigeneticService — Epistemic Epigenetic Detection.

Detects epistemic epigenetics — environmental factors activating
or silencing beliefs without changing their content.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EPIGENETIC_SYSTEM = """You are an epistemic epigenetic specialist. Given a belief activation pattern, assess whether environmental factors activate or silence beliefs:

Key concepts:
- Epistemic epigenetics: environment activating/silencing beliefs
- Environmental activation: environment triggering belief expression
- Contextual silencing: context suppressing belief expression
- Expression without change: activation without content change
- Social environment effect: social environment controlling expression
- Situational triggering: situations triggering dormant beliefs
- Conditional expression: beliefs expressed only in certain conditions

When epistemic epigenetics IS present:
- Environmental factors activating dormant beliefs
- Context silencing beliefs without changing them
- Beliefs activated without their content changing
- Social environment controlling which beliefs express
- Situations triggering expression of dormant beliefs
- Beliefs expressed only under certain conditions
- Environment determining belief expression pattern

When stable expression is present:
- Beliefs expressed consistently regardless of environment
- Context does not inappropriately silence beliefs
- Belief expression based on relevance not environment
- Social environment not controlling expression
- Beliefs available regardless of situation
- Expression based on appropriateness not conditioning
- Consistent belief expression pattern

Output JSON with: epigenetic_present (bool), severity (none/mild/moderate/severe), belief (what belief is affected), environment (what environment triggers/silences), activation (how activation works), silencing (how silencing works), recommendation (stable_expression/mild_environmental_influence/significant_epigenetic/major_environmental_control/restore_autonomous_expression)."""

EPISTEMIC_EPIGENETIC_PROMPT = """Detect epistemic epigenetics:

Belief: {belief}
Environment: {environment}
Activation: {activation}
Silencing: {silencing}
Domain: {domain}
Context: {context}

Are environmental factors activating or silencing beliefs without changing their content? Return ONLY valid JSON."""


class EpistemicEpigeneticService:
    """Detects epistemic epigenetics — environment controlling belief expression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        environment: str = "",
        activation: str = "",
        silencing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic epigenetics."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EPIGENETIC_PROMPT.format(
                belief=belief,
                environment=environment or "Not specified",
                activation=activation or "Not specified",
                silencing=silencing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EPIGENETIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "epigenetic_present": data.get("epigenetic_present", False),
            "severity": data.get("severity", ""),
            "environment": data.get("environment", ""),
            "activation": data.get("activation", ""),
            "silencing": data.get("silencing", ""),
            "recommendation": data.get("recommendation", ""),
        }

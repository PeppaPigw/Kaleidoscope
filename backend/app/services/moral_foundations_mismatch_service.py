"""MoralFoundationsMismatchService — Moral Foundations Mismatch Detection.

Detects moral foundations mismatch — disagreements arising from
different moral foundations (Haidt, 2012) rather than factual
disagreement. When people operate from different moral foundations,
they may talk past each other while believing the disagreement is
about facts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_FOUNDATIONS_SYSTEM = """You are a moral foundations mismatch specialist. Given a disagreement, assess whether it stems from different moral foundations rather than factual disagreement:

Key concepts (Haidt, 2012):
- Moral foundations: care/harm, fairness/cheating, loyalty/betrayal, authority/subversion, sanctity/degradation, liberty/oppression
- Foundation mismatch: parties prioritize different foundations
- Talking past each other: disagreement appears factual but is foundational
- Moral taste buds: different people weight foundations differently
- Political divide: liberals emphasize care/fairness, conservatives use all six
- Moral dumbfounding: strong moral intuition without articulable reasons
- Is-ought confusion: deriving values from facts or vice versa

When moral foundations mismatch IS present:
- Parties disagree but can't identify a factual crux
- Each side finds the other's position morally incomprehensible
- The disagreement persists despite agreement on facts
- Different moral foundations are being prioritized
- "How can they not see this is wrong?" from both sides
- Arguments that persuade one side have no effect on the other
- The disagreement maps onto known foundation differences

When disagreement IS factual:
- There's a specific factual claim that would resolve the disagreement
- Both parties agree on the moral framework but disagree on facts
- Evidence could in principle settle the dispute
- The disagreement doesn't map onto foundation differences
- Both parties can articulate what evidence would change their mind
- The moral intuitions align but empirical beliefs differ
- A bet could be constructed to test the disagreement

Output JSON with: foundations_mismatch_present (bool), severity (none/mild/moderate/severe), disagreement (what is disagreed about), foundation_a (what foundation party A prioritizes), foundation_b (what foundation party B prioritizes), factual_component (is there a factual component), resolution_path (how could this be resolved), recommendation (disagreement_factual/mild_foundation_difference/significant_moral_mismatch/major_talking_past/identify_foundation_difference)."""

MORAL_FOUNDATIONS_PROMPT = """Detect moral foundations mismatch:

Disagreement: {disagreement}
Party A's reasoning: {party_a}
Party B's reasoning: {party_b}
Factual component: {factual}
Domain: {domain}
Context: {context}

Does this disagreement stem from different moral foundations rather than factual disagreement? Return ONLY valid JSON."""


class MoralFoundationsMismatchService:
    """Detects moral foundations mismatch — disagreements from different foundations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        party_a: str = "",
        party_b: str = "",
        factual: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral foundations mismatch."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_FOUNDATIONS_PROMPT.format(
                disagreement=disagreement,
                party_a=party_a or "Not specified",
                party_b=party_b or "Not specified",
                factual=factual or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_FOUNDATIONS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "foundations_mismatch_present": data.get("foundations_mismatch_present", False),
            "severity": data.get("severity", ""),
            "foundation_a": data.get("foundation_a", ""),
            "foundation_b": data.get("foundation_b", ""),
            "factual_component": data.get("factual_component", ""),
            "resolution_path": data.get("resolution_path", ""),
            "recommendation": data.get("recommendation", ""),
        }

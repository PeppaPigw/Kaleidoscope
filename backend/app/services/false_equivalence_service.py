"""FalseEquivalenceService — False Equivalence Detection.

Detects false equivalence — treating two things as comparable or
equal when they differ in important ways. Often used to create
a misleading impression of balance between positions of vastly
different evidential support or moral weight.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_EQUIVALENCE_SYSTEM = """You are a false equivalence specialist. Given a comparison, assess whether it treats unequal things as equal:

Key concepts:
- False equivalence: equating things that differ in important ways
- False balance: giving equal weight to unequal positions
- Bothsidesism: treating all perspectives as equally valid
- Category error: comparing things from different categories
- Degree matters: differences in degree can be differences in kind
- Asymmetric comparison: ignoring relevant differences
- Legitimate comparison: things can be compared without being equated

When false equivalence IS present:
- Equating a minor issue with a major one as if they're the same
- "Both sides are equally bad" when one is clearly worse
- Comparing isolated incidents to systematic patterns
- Treating fringe views as equivalent to scientific consensus
- "What about X?" when X is categorically different
- Ignoring scale, severity, or frequency differences
- Creating false balance in reporting/analysis

When false equivalence is NOT present:
- The comparison acknowledges relevant differences
- The things compared are genuinely similar in relevant respects
- Differences in degree are noted alongside similarities
- The comparison is about a specific shared feature, not overall equivalence
- Both positions genuinely have comparable evidence
- The comparison is used to illuminate, not to equate
- Relevant asymmetries are discussed

Output JSON with: false_equivalence_present (bool), severity (none/mild/moderate/severe), comparison (what is being compared), thing_a (first item), thing_b (second item), key_differences (important differences ignored), legitimate_similarity (what they do share), recommendation (no_false_equivalence/mild_oversimplification/significant_false_equivalence/major_false_balance/acknowledge_differences)."""

FALSE_EQUIVALENCE_PROMPT = """Detect false equivalence:

Comparison: {comparison}
Thing A: {thing_a}
Thing B: {thing_b}
Claimed similarity: {similarity}
Domain: {domain}
Context: {context}

Does this treat unequal things as equivalent while ignoring important differences? Return ONLY valid JSON."""


class FalseEquivalenceService:
    """Detects false equivalence — treating unequal things as equal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comparison: str,
        *,
        thing_a: str = "",
        thing_b: str = "",
        similarity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false equivalence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_EQUIVALENCE_PROMPT.format(
                comparison=comparison,
                thing_a=thing_a or "Not specified",
                thing_b=thing_b or "Not specified",
                similarity=similarity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_EQUIVALENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comparison": comparison[:200],
            "false_equivalence_present": data.get("false_equivalence_present", False),
            "severity": data.get("severity", ""),
            "thing_a": data.get("thing_a", ""),
            "thing_b": data.get("thing_b", ""),
            "key_differences": data.get("key_differences", ""),
            "recommendation": data.get("recommendation", ""),
        }

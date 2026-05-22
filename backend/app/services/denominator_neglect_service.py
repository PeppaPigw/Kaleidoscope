"""DenominatorNeglectService — Denominator Neglect Detection.

Detects denominator neglect — focusing on the numerator
(number of events) while ignoring the denominator (total
opportunities). Reyna & Brainerd (2008). "100 people died"
sounds worse than "100 out of 10 million" even though the
rate is tiny. People respond to absolute numbers rather than
proportions, leading to distorted risk perception.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DENOMINATOR_NEGLECT_SYSTEM = """You are a denominator neglect specialist. Given a judgment about frequency, risk, or probability, assess whether the denominator is being ignored:

Key concepts (Reyna & Brainerd, 2008):
- Denominator neglect: focusing on counts, ignoring base
- Numerator focus: absolute numbers dominate perception
- Rate vs count confusion: "more cases" vs "higher rate"
- Frequency format effect: 1 in 10 vs 10% perceived differently
- Ratio bias: 9/100 seems larger than 1/10
- Population scaling: failing to adjust for population size
- Base rate neglect interaction: ignoring the reference class size

When denominator neglect IS present:
- "100 incidents!" without mentioning out of how many total
- Comparing raw counts between groups of different sizes
- Risk perception driven by absolute numbers not rates
- "More people die from X than Y" without per-capita adjustment
- Choosing 9/100 over 1/10 because 9 > 1
- News reporting counts without context of base rates
- "Cases are rising" without noting the denominator also changed

When absolute numbers ARE appropriate:
- The total impact matters regardless of rate (resource allocation)
- The denominator is constant across comparisons
- The audience needs to understand total burden
- Rate-based thinking would obscure genuine scale differences
- The decision depends on absolute capacity, not proportions

Output JSON with: denominator_neglect_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), numerator (what count is being focused on), denominator (what base is being ignored), actual_rate (what is the actual rate/proportion), distortion (how much does ignoring denominator distort), comparison_issue (are unequal bases being compared), recommendation (absolute_numbers_appropriate/mild_denominator_neglect/significant_rate_confusion/major_denominator_ignored/calculate_and_compare_rates)."""

DENOMINATOR_NEGLECT_PROMPT = """Detect denominator neglect:

Judgment: {judgment}
Numbers cited: {numbers}
Base/denominator: {base}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is the denominator being ignored, causing distorted perception of frequency or risk? Return ONLY valid JSON."""


class DenominatorNeglectService:
    """Detects denominator neglect — ignoring the base when evaluating counts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        numbers: str = "",
        base: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect denominator neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DENOMINATOR_NEGLECT_PROMPT.format(
                judgment=judgment,
                numbers=numbers or "Not specified",
                base=base or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DENOMINATOR_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "denominator_neglect_present": data.get("denominator_neglect_present", False),
            "severity": data.get("severity", ""),
            "numerator": data.get("numerator", ""),
            "denominator": data.get("denominator", ""),
            "actual_rate": data.get("actual_rate", ""),
            "distortion": data.get("distortion", ""),
            "comparison_issue": data.get("comparison_issue", ""),
            "recommendation": data.get("recommendation", ""),
        }

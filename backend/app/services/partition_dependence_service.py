"""PartitionDependenceService — Partition Dependence Detection.

Detects partition dependence — judgments and allocations that
change based on how options are categorized or grouped, even
when the underlying options are the same. Fox & Clemen (2005).
How you slice the pie affects how much you put in each slice.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PARTITION_DEPENDENCE_SYSTEM = """You are a partition dependence specialist. Given a judgment or allocation, assess whether the categorization scheme is inappropriately influencing the decision:

Key concepts (Fox & Clemen, 2005):
- Partition dependence: judgments change with categorization
- Implicit 1/n: equal weight to each category regardless of size
- Category salience: prominent categories get more weight
- Granularity effect: finer partitions get more total weight
- Unpacking effect: detailed descriptions get higher probability
- Support theory interaction: evidence for hypothesis depends on description
- Framing through categorization: how you group affects what you choose

When partition dependence IS present:
- Probability estimates that change when events are grouped differently
- Budget allocations driven by number of categories, not importance
- "We have 5 departments so each gets 20%" regardless of need
- Risk assessments that change when risks are categorized differently
- More detailed breakdowns getting higher total probability
- Attention allocation driven by how information is organized

When the partition IS appropriate:
- Categories reflect genuine structural differences
- The partition captures meaningful distinctions
- Allocation would be the same under alternative groupings
- The person has considered alternative categorizations
- The granularity matches the decision needs

Output JSON with: partition_dependence_present (bool), severity (none/mild/moderate/severe), judgment (what judgment or allocation is being made), partition (how are options categorized), alternative_partition (how else could they be categorized), would_change (would the judgment change with different partition?), category_count_effect (is the number of categories driving allocation?), granularity_bias (is finer detail getting more weight?), recommendation (partition_appropriate/mild_dependence/significant_category_driven/major_partition_dependence/test_alternative_partitions)."""

PARTITION_DEPENDENCE_PROMPT = """Detect partition dependence:

Judgment: {judgment}
Categories: {categories}
Allocation: {allocation}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is the categorization scheme inappropriately influencing the judgment? Return ONLY valid JSON."""


class PartitionDependenceService:
    """Detects partition dependence — categorization scheme driving judgments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        categories: str = "",
        allocation: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect partition dependence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PARTITION_DEPENDENCE_PROMPT.format(
                judgment=judgment,
                categories=categories or "Not specified",
                allocation=allocation or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PARTITION_DEPENDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "partition_dependence_present": data.get("partition_dependence_present", False),
            "severity": data.get("severity", ""),
            "alternative_partition": data.get("alternative_partition", ""),
            "would_change": data.get("would_change", ""),
            "category_count_effect": data.get("category_count_effect", ""),
            "granularity_bias": data.get("granularity_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }

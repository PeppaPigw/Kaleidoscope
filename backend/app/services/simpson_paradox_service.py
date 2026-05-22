"""SimpsonParadoxService — Simpson's Paradox Detection.

Detects Simpson's Paradox — when a trend that appears in several
groups reverses when the groups are combined. Can completely reverse
conclusions from data. Critical for causal inference, policy
evaluation, and any aggregated statistics.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SIMPSON_SYSTEM = """You are a Simpson's Paradox specialist. Given a data claim or statistical finding, assess whether Simpson's Paradox might be reversing the true relationship:

Key concepts:
- Simpson's Paradox: a trend in subgroups reverses when groups are combined
- Lurking variable: a confounding variable that creates the reversal
- Ecological fallacy: inferring individual behavior from group-level data
- Aggregation bias: combining heterogeneous groups masks true relationships
- Causal structure: the direction of causation determines which level is correct
- Collider bias: conditioning on a common effect creates spurious associations

Classic examples:
- UC Berkeley gender bias: overall admission favored men, but within each department women were admitted at equal or higher rates (women applied to more competitive departments)
- Kidney stone treatment: Treatment A better overall, Treatment B better for both small and large stones (Treatment A was used on easier cases)

When Simpson's Paradox IS likely:
- Groups differ in size or composition
- A confounding variable correlates with both the grouping and the outcome
- Aggregated data tells a different story than disaggregated data
- Causal pathways run through the grouping variable

When the aggregate IS correct:
- No lurking variable exists
- The grouping variable is not causally relevant
- Random assignment ensures balance

Output JSON with: simpson_paradox_present (bool), severity (none/mild/moderate/severe), group_level_trend (what the data shows within groups), aggregate_trend (what the combined data shows), direction_reversal (bool — does the trend actually flip?), lurking_variable (what confounding variable creates the reversal), causal_structure (how the variables are causally related), correct_interpretation (which level — group or aggregate — gives the right answer and why), ecological_fallacy_risk (bool), aggregation_method (how groups are being combined), group_composition (how groups differ in size/makeup), base_rate_difference (do groups have different base rates?), policy_implication (how the paradox affects decisions), disaggregation_needed (what subgroups should be examined separately), recommendation (no_paradox/possible_paradox/likely_paradox/confirmed_paradox/disaggregate_immediately)."""

SIMPSON_PROMPT = """Detect Simpson's Paradox:

Data claim: {data_claim}
Groups/subgroups: {groups}
Aggregation method: {aggregation}
Potential confounders: {confounders}
Domain: {domain}
Context: {context}

Could Simpson's Paradox be reversing the true relationship? Return ONLY valid JSON."""


class SimpsonParadoxService:
    """Detects Simpson's Paradox — trend reversal between subgroups and aggregate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        data_claim: str,
        *,
        groups: str = "",
        aggregation: str = "",
        confounders: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Simpson's Paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SIMPSON_PROMPT.format(
                data_claim=data_claim,
                groups=groups or "Not specified",
                aggregation=aggregation or "Not specified",
                confounders=confounders or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SIMPSON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "data_claim": data_claim[:200],
            "simpson_paradox_present": data.get("simpson_paradox_present", False),
            "severity": data.get("severity", ""),
            "group_level_trend": data.get("group_level_trend", ""),
            "aggregate_trend": data.get("aggregate_trend", ""),
            "direction_reversal": data.get("direction_reversal", False),
            "lurking_variable": data.get("lurking_variable", ""),
            "causal_structure": data.get("causal_structure", ""),
            "correct_interpretation": data.get("correct_interpretation", ""),
            "ecological_fallacy_risk": data.get("ecological_fallacy_risk", False),
            "aggregation_method": data.get("aggregation_method", ""),
            "group_composition": data.get("group_composition", ""),
            "base_rate_difference": data.get("base_rate_difference", ""),
            "policy_implication": data.get("policy_implication", ""),
            "disaggregation_needed": data.get("disaggregation_needed", ""),
            "recommendation": data.get("recommendation", ""),
        }

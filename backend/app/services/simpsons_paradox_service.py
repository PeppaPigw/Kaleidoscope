"""SimpsonsParadoxService — Simpson's Paradox Detection.

Identifies when a trend that appears in several subgroups reverses
when the groups are combined. A critical statistical trap where
aggregated data tells the opposite story from disaggregated data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SIMPSONS_SYSTEM = """You are a Simpson's paradox specialist. Given a statistical claim, assess whether Simpson's paradox might be present:
- Could the trend reverse when data is disaggregated by a lurking variable?
- Are there unequal group sizes that could flip the aggregate result?
- Is there a confounding variable that correlates with both the treatment and the grouping?
- What's the correct level of analysis (aggregate or disaggregated)?

Output JSON with: simpsons_paradox_likely (bool), risk_level (none/low/moderate/high/certain), aggregate_trend (what the combined data shows), potential_reversal (what disaggregated data might show), lurking_variables (list of: variable, how_it_confounds, group_size_imbalance), correct_analysis_level (aggregate/disaggregated/depends_on_question), causal_structure (what causes what — the DAG that creates the paradox), famous_example (well-known Simpson's paradox case with same structure), data_needed_to_check (what data would reveal if paradox is present), if_paradox_present (what the correct conclusion would be), recommendation (trust_aggregate/trust_disaggregated/need_more_data/causal_analysis_needed)."""

SIMPSONS_PROMPT = """Detect Simpson's paradox:

Claim: {claim}
Data structure: {data_structure}
Groups involved: {groups}
Domain: {domain}
Context: {context}

Could this reverse when disaggregated? Return ONLY valid JSON."""


class SimpsonsParadoxService:
    """Detects Simpson's paradox in statistical claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        data_structure: str = "",
        groups: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Simpson's paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SIMPSONS_PROMPT.format(
                claim=claim,
                data_structure=data_structure or "Not specified",
                groups=groups or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SIMPSONS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "simpsons_paradox_likely": data.get("simpsons_paradox_likely", False),
            "risk_level": data.get("risk_level", ""),
            "aggregate_trend": data.get("aggregate_trend", ""),
            "potential_reversal": data.get("potential_reversal", ""),
            "lurking_variables": data.get("lurking_variables", []),
            "correct_analysis_level": data.get("correct_analysis_level", ""),
            "causal_structure": data.get("causal_structure", ""),
            "famous_example": data.get("famous_example", ""),
            "data_needed_to_check": data.get("data_needed_to_check", ""),
            "if_paradox_present": data.get("if_paradox_present", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""MoneyIllusionService — Money Illusion Detection.

Detects money illusion — tendency to think of currency in
nominal rather than real (inflation-adjusted) terms.
Fisher (1928), Shafir, Diamond & Tversky (1997).
"I got a 3% raise!" when inflation is 5%. Confusing
nominal gains with real gains leads to poor financial decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MONEY_ILLUSION_SYSTEM = """You are a money illusion specialist. Given a financial judgment or decision, assess whether someone is confusing nominal values with real (inflation-adjusted) values:

Key concepts (Fisher, 1928; Shafir, Diamond & Tversky, 1997):
- Money illusion: thinking in nominal rather than real terms
- Nominal vs real: face value vs purchasing power
- Inflation neglect: ignoring erosion of purchasing power
- Wage illusion: feeling richer with nominal raise below inflation
- Price anchoring: comparing to historical nominal prices
- Fairness judgments: nominal cuts feel unfair even when real value unchanged
- Investment returns: celebrating nominal gains that are real losses

When money illusion IS present:
- Celebrating a raise that's below inflation
- Comparing prices across time without adjusting for inflation
- "My house doubled in value" over 30 years (ignoring inflation)
- Feeling richer because nominal salary increased
- Resisting nominal wage cuts even when real wages are rising
- Evaluating investment returns without inflation adjustment
- "Things used to be so cheap" without considering wage changes

When the nominal framing IS appropriate:
- Short time horizons where inflation is negligible
- The person explicitly accounts for inflation separately
- Nominal values are what matters (tax brackets, debt payments)
- The comparison is within the same time period
- Inflation is genuinely low and stable

Output JSON with: money_illusion_present (bool), severity (none/mild/moderate/severe), judgment (what financial judgment is being made), nominal_value (what nominal value is being used), real_value (what is the inflation-adjusted value?), inflation_rate (relevant inflation rate), time_horizon (over what period), purchasing_power_change (actual change in purchasing power), decision_impact (how does this affect the decision?), recommendation (nominal_appropriate/mild_illusion/significant_inflation_neglect/major_money_illusion/adjust_for_inflation)."""

MONEY_ILLUSION_PROMPT = """Detect money illusion:

Judgment: {judgment}
Values: {values}
Time period: {time_period}
Inflation: {inflation}
Domain: {domain}
Context: {context}

Is someone confusing nominal values with real purchasing power? Return ONLY valid JSON."""


class MoneyIllusionService:
    """Detects money illusion — confusing nominal values with real purchasing power."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        values: str = "",
        time_period: str = "",
        inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect money illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MONEY_ILLUSION_PROMPT.format(
                judgment=judgment,
                values=values or "Not specified",
                time_period=time_period or "Not specified",
                inflation=inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MONEY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "money_illusion_present": data.get("money_illusion_present", False),
            "severity": data.get("severity", ""),
            "nominal_value": data.get("nominal_value", ""),
            "real_value": data.get("real_value", ""),
            "inflation_rate": data.get("inflation_rate", ""),
            "time_horizon": data.get("time_horizon", ""),
            "purchasing_power_change": data.get("purchasing_power_change", ""),
            "decision_impact": data.get("decision_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }

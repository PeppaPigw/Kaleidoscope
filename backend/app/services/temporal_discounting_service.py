"""TemporalDiscountingService — Temporal Discounting Bias Detection.

Detects excessive temporal discounting — devaluing future
rewards relative to immediate ones beyond what's rational.
Related to but distinct from hyperbolic discounting. Focuses
on whether the discount rate applied to future outcomes is
appropriate given the actual uncertainty and opportunity cost.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_DISCOUNTING_SYSTEM = """You are a temporal discounting specialist. Given a decision involving tradeoffs between present and future outcomes, assess whether future outcomes are being excessively devalued:

Key concepts:
- Temporal discounting: reducing value of future outcomes
- Excessive discounting: devaluing future more than uncertainty warrants
- Present bias: overweighting immediate gratification
- Delay aversion: avoiding waiting even when waiting is optimal
- Myopic decision-making: short time horizon in planning
- Intergenerational discounting: devaluing outcomes for future people
- Rational discounting: appropriate adjustment for uncertainty and opportunity cost

When excessive discounting IS present:
- Choosing immediate small reward over much larger delayed reward
- Ignoring long-term consequences for short-term gains
- "Future me can deal with it" when future costs far exceed present benefits
- Discount rate far exceeds actual uncertainty or opportunity cost
- Systematically underinvesting in future outcomes
- "A bird in the hand" applied even when the bush has many more birds

When the discounting IS rational:
- Genuine uncertainty about whether the future reward will materialize
- Opportunity cost of waiting is properly calculated
- The discount rate matches actual risk of non-delivery
- Liquidity constraints make immediate value genuinely more useful
- The future outcome depends on factors outside one's control

Output JSON with: excessive_discounting_present (bool), severity (none/mild/moderate/severe), decision (what tradeoff is being made), immediate_value (value of the immediate option), future_value (value of the future option), time_horizon (how far in the future), discount_rate_applied (implicit discount rate), rational_discount_rate (what would be rational given uncertainty), uncertainty_level (how uncertain is the future outcome?), opportunity_cost (what is genuinely lost by waiting?), present_bias (bool — is present bias driving the decision?), recommendation (discounting_rational/mild_excess/significant_myopia/major_present_bias/recalculate_with_rational_rate)."""

TEMPORAL_DISCOUNTING_PROMPT = """Detect excessive temporal discounting:

Decision: {decision}
Immediate option: {immediate}
Future option: {future}
Time horizon: {horizon}
Domain: {domain}
Context: {context}

Is the future being excessively devalued relative to rational discounting? Return ONLY valid JSON."""


class TemporalDiscountingService:
    """Detects excessive temporal discounting — irrational devaluation of future outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        immediate: str = "",
        future: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect excessive temporal discounting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_DISCOUNTING_PROMPT.format(
                decision=decision,
                immediate=immediate or "Not specified",
                future=future or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_DISCOUNTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "excessive_discounting_present": data.get("excessive_discounting_present", False),
            "severity": data.get("severity", ""),
            "immediate_value": data.get("immediate_value", ""),
            "future_value": data.get("future_value", ""),
            "time_horizon": data.get("time_horizon", ""),
            "discount_rate_applied": data.get("discount_rate_applied", ""),
            "rational_discount_rate": data.get("rational_discount_rate", ""),
            "uncertainty_level": data.get("uncertainty_level", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "present_bias": data.get("present_bias", False),
            "recommendation": data.get("recommendation", ""),
        }

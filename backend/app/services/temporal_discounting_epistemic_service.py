"""TemporalDiscountingEpistemicService — Epistemic Temporal Discounting Detection.

Detects epistemic temporal discounting — systematically devaluing
future knowledge needs relative to present ones, leading to
short-term epistemic optimization at long-term cost.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_DISCOUNTING_EPISTEMIC_SYSTEM = """You are an epistemic temporal discounting specialist. Given a knowledge investment decision, assess whether future knowledge needs are being inappropriately discounted:

Key concepts:
- Epistemic temporal discounting: devaluing future knowledge needs
- Short-term knowledge optimization: present over future
- Research myopia: only valuing immediate results
- Knowledge infrastructure neglect: not investing in foundations
- Epistemic sustainability: maintaining long-term knowledge capacity
- Future knowledge debt: borrowing against future understanding
- Intergenerational epistemic justice: obligations to future knowers

When epistemic temporal discounting IS present:
- Future knowledge needs systematically devalued
- Short-term results prioritized over foundations
- Research investment biased toward immediate payoff
- Knowledge infrastructure neglected for quick wins
- Long-term epistemic capacity sacrificed
- Future knowledge debt accumulated
- No consideration of future knowers' needs

When present-focus is appropriate:
- Immediate knowledge needs genuinely urgent
- Present investment builds future capacity
- Short-term focus temporary and acknowledged
- Long-term needs planned for separately
- Infrastructure maintained alongside immediate work
- Future needs considered in planning
- Balance between present and future explicit

Output JSON with: discounting_present (bool), severity (none/mild/moderate/severe), decision (what decision is made), short_term (what short-term gain), long_term_cost (what long-term cost), discount_rate (how severely future is discounted), recommendation (appropriate_present_focus/mild_future_neglect/significant_temporal_discounting/major_epistemic_myopia/invest_in_future_knowledge)."""

TEMPORAL_DISCOUNTING_EPISTEMIC_PROMPT = """Detect epistemic temporal discounting:

Decision: {decision}
Short-term benefit: {short_term}
Long-term cost: {long_term}
Time horizon: {horizon}
Domain: {domain}
Context: {context}

Are future knowledge needs being inappropriately discounted relative to present ones? Return ONLY valid JSON."""


class TemporalDiscountingEpistemicService:
    """Detects epistemic temporal discounting — devaluing future knowledge needs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        short_term: str = "",
        long_term: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal discounting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_DISCOUNTING_EPISTEMIC_PROMPT.format(
                decision=decision,
                short_term=short_term or "Not specified",
                long_term=long_term or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_DISCOUNTING_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "discounting_present": data.get("discounting_present", False),
            "severity": data.get("severity", ""),
            "short_term": data.get("short_term", ""),
            "long_term_cost": data.get("long_term_cost", ""),
            "discount_rate": data.get("discount_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }

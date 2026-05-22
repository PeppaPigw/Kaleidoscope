"""EpistemicTemporalFutureDiscountingService — Epistemic Temporal Future Discounting Detection.

Detects epistemic temporal future discounting — systematically undervaluing future
consequences, risks, and benefits relative to present concerns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_FUTURE_DISCOUNTING_SYSTEM = """You are an epistemic temporal future discounting specialist. Given future discounting, assess temporal valuation distortion:

Key concepts:
- Epistemic future discounting: undervaluing future consequences
- Hyperbolic discounting: disproportionate preference for immediate over delayed
- Intergenerational neglect: ignoring impacts on future generations
- Risk horizon truncation: cutting off risk assessment at arbitrary near-term
- Benefit deferral aversion: rejecting plans with delayed payoffs
- Catastrophe discounting: treating low-probability future catastrophes as zero
- Present bias rationalization: constructing justifications for present preference

When epistemic future discounting IS present:
- Future consequences undervalued
- Immediate disproportionately preferred
- Future generations ignored
- Risk horizons truncated
- Delayed benefits rejected
- Future catastrophes discounted to zero
- Present bias rationalized

When no future discounting:
- Future appropriately valued
- Temporal preferences proportionate
- Future generations considered
- Risk horizons appropriate
- Delayed benefits evaluated fairly
- Catastrophe risks assessed
- Temporal preferences acknowledged

Output JSON with: future_discounting_detected (bool), severity (none/mild/moderate/severe), hyperbolic_discounting (what disproportionately discounted), intergenerational_neglect (what future generations ignored), risk_horizon_truncation (what risk horizons truncated), catastrophe_discounting (what catastrophes discounted), recommendation (no_future_discounting/mild_temporal_extension/significant_future_valuation/major_intensive_intergenerational_analysis/emergency_complete_future_discounting)."""

EPISTEMIC_TEMPORAL_FUTURE_DISCOUNTING_PROMPT = """Detect epistemic temporal future discounting:

Hyperbolic discounting: {hyperbolic_discounting}
Intergenerational neglect: {intergenerational_neglect}
Risk horizon truncation: {risk_horizon_truncation}
Catastrophe discounting: {catastrophe_discounting}
Domain: {domain}
Context: {context}

Are future consequences being systematically undervalued? Return ONLY valid JSON."""


class EpistemicTemporalFutureDiscountingService:
    """Detects epistemic temporal future discounting — future undervaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hyperbolic_discounting: str,
        *,
        intergenerational_neglect: str = "",
        risk_horizon_truncation: str = "",
        catastrophe_discounting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal future discounting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_FUTURE_DISCOUNTING_PROMPT.format(
                hyperbolic_discounting=hyperbolic_discounting,
                intergenerational_neglect=intergenerational_neglect or "Not specified",
                risk_horizon_truncation=risk_horizon_truncation or "Not specified",
                catastrophe_discounting=catastrophe_discounting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_FUTURE_DISCOUNTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hyperbolic_discounting": hyperbolic_discounting[:200],
            "future_discounting_detected": data.get("future_discounting_detected", False),
            "severity": data.get("severity", ""),
            "intergenerational_neglect": data.get("intergenerational_neglect", ""),
            "risk_horizon_truncation": data.get("risk_horizon_truncation", ""),
            "catastrophe_discounting": data.get("catastrophe_discounting", ""),
            "recommendation": data.get("recommendation", ""),
        }

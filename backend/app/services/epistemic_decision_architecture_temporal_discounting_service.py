"""EpistemicDecisionArchitectureTemporalDiscountingService — Temporal Discounting Detection.

Detects hyperbolic discounting distorting time-preference decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ARCHITECTURE_TEMPORAL_DISCOUNTING_SYSTEM = """You are an epistemic decision architecture temporal discounting specialist. Given present bias, assess whether hyperbolic discounting is distorting time-preference decisions:

Key concepts:
- Temporal discounting: undervaluing delayed outcomes relative to immediate ones
- Present bias: overweighting immediate costs and benefits
- Future self neglect: failing to treat future needs as decision-relevant
- Immediacy premium: overvaluing options because they pay off now
- Delayed gratification failure: inability to choose better delayed outcomes

When temporal discounting IS present:
- Immediate rewards dominate larger future value
- Future self interests are neglected
- Immediacy receives unjustified premium
- Delayed gratification fails despite better long-term fit

When no temporal discounting:
- Time horizons are explicit
- Future outcomes receive appropriate weight
- Immediate and delayed outcomes are compared consistently
- Commitment or planning mechanisms protect long-term goals

Output JSON with: temporal_discounting_detected (bool), severity (none/mild/moderate/severe), future_self_neglect (how future self is neglected), immediacy_premium (how immediate payoff is overvalued), delayed_gratification_failure (how delayed gratification fails), recommendation (no_temporal_discounting/mild_time_horizon_review/significant_future_weighting/major_commitment_design/emergency_present_bias_reset)."""

EPISTEMIC_DECISION_ARCHITECTURE_TEMPORAL_DISCOUNTING_PROMPT = """Detect decision architecture temporal discounting:

Present bias: {present_bias}
Future self neglect: {future_self_neglect}
Immediacy premium: {immediacy_premium}
Delayed gratification failure: {delayed_gratification_failure}
Domain: {domain}
Context: {context}

Is hyperbolic discounting distorting time-preference decisions? Return ONLY valid JSON."""


class EpistemicDecisionArchitectureTemporalDiscountingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        present_bias: str,
        *,
        future_self_neglect: str = "",
        immediacy_premium: str = "",
        delayed_gratification_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ARCHITECTURE_TEMPORAL_DISCOUNTING_PROMPT.format(
                present_bias=present_bias,
                future_self_neglect=future_self_neglect or "Not specified",
                immediacy_premium=immediacy_premium or "Not specified",
                delayed_gratification_failure=delayed_gratification_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ARCHITECTURE_TEMPORAL_DISCOUNTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "present_bias": present_bias[:200],
            "temporal_discounting_detected": data.get("temporal_discounting_detected", False),
            "severity": data.get("severity", ""),
            "future_self_neglect": data.get("future_self_neglect", ""),
            "immediacy_premium": data.get("immediacy_premium", ""),
            "delayed_gratification_failure": data.get("delayed_gratification_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }

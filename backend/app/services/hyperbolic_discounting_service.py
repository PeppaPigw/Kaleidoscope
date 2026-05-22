"""HyperbolicDiscountingService — Temporal Discounting Detection.

Detects hyperbolic discounting — the irrational tendency to prefer
smaller immediate rewards over larger delayed ones, with discount
rates that decrease over time (unlike exponential discounting).
Explains procrastination, addiction, undersaving, climate inaction,
and preference reversals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HYPERBOLIC_SYSTEM = """You are a temporal discounting specialist. Given a decision involving tradeoffs between present and future, assess whether hyperbolic discounting is distorting judgment:

Key concepts:
- Hyperbolic discounting: discount rate decreases with delay (unlike rational exponential discounting)
- Present bias: overweighting immediate outcomes relative to future ones
- Preference reversal: choosing A over B when both are distant, but B over A when B becomes immediate
- Commitment devices: mechanisms to bind future self to current preferences
- Temporal inconsistency: plans made for the future that won't be followed when the future arrives

Output JSON with: hyperbolic_discounting_present (bool), severity (none/mild/moderate/severe/extreme), present_bias_strength (0-1 — how much the present is overweighted), immediate_reward (what is gained now), delayed_reward (what would be gained later), rational_choice (what exponential discounting would recommend), actual_choice (what is being chosen), preference_reversal_likely (bool — would the choice flip if both options were pushed into the future?), discount_rate_near (implied discount rate for near-term), discount_rate_far (implied discount rate for far-term), time_horizon (how far into the future the delayed reward is), commitment_device_available (bool — can the decision-maker bind themselves?), commitment_device_suggestion (what commitment device would help), procrastination_risk (0-1), addiction_pattern (bool — does this resemble addictive discounting?), collective_action_dimension (bool — is this a collective hyperbolic discounting problem like climate?), who_exploits (who benefits from others' present bias), nudge_opportunity (how to help without restricting choice), recommendation (discount_appropriate/mild_present_bias/significant_distortion/commitment_device_needed/structural_intervention_needed)."""

HYPERBOLIC_PROMPT = """Detect hyperbolic discounting:

Decision: {decision}
Immediate option: {immediate}
Delayed option: {delayed}
Time horizon: {time_horizon}
Domain: {domain}
Context: {context}

Is hyperbolic discounting distorting this decision? Return ONLY valid JSON."""


class HyperbolicDiscountingService:
    """Detects hyperbolic discounting and present bias."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        immediate: str = "",
        delayed: str = "",
        time_horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hyperbolic discounting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HYPERBOLIC_PROMPT.format(
                decision=decision,
                immediate=immediate or "Not specified",
                delayed=delayed or "Not specified",
                time_horizon=time_horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HYPERBOLIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "hyperbolic_discounting_present": data.get("hyperbolic_discounting_present", False),
            "severity": data.get("severity", ""),
            "present_bias_strength": data.get("present_bias_strength", 0),
            "immediate_reward": data.get("immediate_reward", ""),
            "delayed_reward": data.get("delayed_reward", ""),
            "rational_choice": data.get("rational_choice", ""),
            "actual_choice": data.get("actual_choice", ""),
            "preference_reversal_likely": data.get("preference_reversal_likely", False),
            "discount_rate_near": data.get("discount_rate_near", ""),
            "discount_rate_far": data.get("discount_rate_far", ""),
            "time_horizon": data.get("time_horizon", ""),
            "commitment_device_available": data.get("commitment_device_available", False),
            "commitment_device_suggestion": data.get("commitment_device_suggestion", ""),
            "procrastination_risk": data.get("procrastination_risk", 0),
            "addiction_pattern": data.get("addiction_pattern", False),
            "collective_action_dimension": data.get("collective_action_dimension", False),
            "who_exploits": data.get("who_exploits", ""),
            "nudge_opportunity": data.get("nudge_opportunity", ""),
            "recommendation": data.get("recommendation", ""),
        }

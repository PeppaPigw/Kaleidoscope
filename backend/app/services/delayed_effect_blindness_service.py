"""DelayedEffectBlindnessService — Delayed Effect Blindness Detection.

Detects delayed effect blindness — ignoring effects that manifest
after significant delay, leading to underestimation of long-term
consequences and overvaluation of immediate results.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DELAYED_EFFECT_BLINDNESS_SYSTEM = """You are a delayed effect blindness specialist. Given an assessment, evaluate whether delayed effects are being ignored:

Key concepts:
- Latency period: time between cause and visible effect
- Accumulation effects: small causes building to large effects over time
- Threshold effects: delayed manifestation until critical mass
- Feedback delays: time for feedback loops to complete cycles
- Intergenerational effects: consequences spanning generations
- Sleeper effects: dormant causes activating later
- Time horizon mismatch: evaluation period shorter than effect period

When delayed effect blindness IS present:
- Only immediate effects considered in evaluation
- Long-term consequences dismissed or ignored
- Evaluation timeframe shorter than effect timeframe
- Accumulation effects not modeled
- Latency periods not accounted for
- Short-term gains prioritized over long-term costs
- Feedback delays not incorporated into predictions

When delayed effects are recognized:
- Both immediate and delayed effects considered
- Appropriate time horizons used for evaluation
- Accumulation and threshold effects modeled
- Latency periods explicitly accounted for
- Long-term monitoring planned
- Discount rates appropriate for context
- Delayed effects weighted in decision-making

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), assessment (what is being evaluated), immediate_focus (what short-term effects are seen), delayed_effects (what long-term effects are missed), time_horizon (evaluation period vs effect period), recommendation (delayed_effects_recognized/mild_temporal_bias/significant_horizon_mismatch/major_delayed_blindness/extend_time_horizon)."""

DELAYED_EFFECT_BLINDNESS_PROMPT = """Detect delayed effect blindness:

Assessment: {assessment}
Time horizon: {time_horizon}
Immediate effects: {immediate}
Known delayed effects: {delayed}
Domain: {domain}
Context: {context}

Are delayed effects being ignored in this assessment? Return ONLY valid JSON."""


class DelayedEffectBlindnessService:
    """Detects delayed effect blindness — ignoring long-latency consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        time_horizon: str = "",
        immediate: str = "",
        delayed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect delayed effect blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DELAYED_EFFECT_BLINDNESS_PROMPT.format(
                assessment=assessment,
                time_horizon=time_horizon or "Not specified",
                immediate=immediate or "Not specified",
                delayed=delayed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DELAYED_EFFECT_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "immediate_focus": data.get("immediate_focus", ""),
            "delayed_effects": data.get("delayed_effects", ""),
            "time_horizon": data.get("time_horizon", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""TrendExtrapolationService — Trend Extrapolation Detection.

Detects blind trend extrapolation — extending current trends
into the future without considering limits, saturation points,
feedback loops, or structural changes that would alter the trend.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TREND_EXTRAPOLATION_SYSTEM = """You are a trend extrapolation specialist. Given a prediction, assess whether trends are being blindly extended:

Key concepts:
- Linear extrapolation: assuming current rate continues unchanged
- S-curves: growth that saturates
- Limits to growth: physical, economic, or social constraints
- Feedback loops: positive or negative feedback altering trends
- Structural breaks: regime changes that invalidate past trends
- Mean reversion: trends that oscillate around an average
- Exponential growth fallacy: assuming exponential growth continues

When blind extrapolation IS present:
- Current trend extended without considering limits
- Linear projection of exponential growth
- No saturation point identified
- Feedback loops ignored
- "If current trends continue..." without questioning if they will
- Physical or logical limits not considered
- Past growth rate assumed to persist indefinitely

When extrapolation is appropriate:
- Limits and saturation points identified
- Feedback loops considered
- Structural factors supporting trend continuation identified
- Multiple scenarios including trend breaks
- S-curve or logistic model used where appropriate
- Confidence decreases with forecast horizon
- Mechanisms sustaining the trend are understood

Output JSON with: blind_extrapolation (bool), severity (none/mild/moderate/severe), trend (what trend is being extended), limits (what constraints exist), saturation (where the trend might saturate), feedback_loops (what could alter the trend), recommendation (appropriate_extrapolation/mild_overextension/significant_blind_extrapolation/major_limits_ignored/model_saturation)."""

TREND_EXTRAPOLATION_PROMPT = """Detect blind trend extrapolation:

Prediction: {prediction}
Current trend: {trend}
Time horizon: {horizon}
Constraints: {constraints}
Domain: {domain}
Context: {context}

Is this trend being blindly extended without considering limits? Return ONLY valid JSON."""


class TrendExtrapolationService:
    """Detects blind trend extrapolation — extending trends without limits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        trend: str = "",
        horizon: str = "",
        constraints: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect blind trend extrapolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TREND_EXTRAPOLATION_PROMPT.format(
                prediction=prediction,
                trend=trend or "Not specified",
                horizon=horizon or "Not specified",
                constraints=constraints or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TREND_EXTRAPOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "blind_extrapolation": data.get("blind_extrapolation", False),
            "severity": data.get("severity", ""),
            "trend": data.get("trend", ""),
            "limits": data.get("limits", ""),
            "saturation": data.get("saturation", ""),
            "recommendation": data.get("recommendation", ""),
        }

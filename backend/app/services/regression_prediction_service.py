"""RegressionPredictionService — Regression Prediction Detection.

Detects failure to predict regression to the mean — when
extreme observations are expected to continue rather than
reverting toward the average. This leads to overreaction
to outliers and poor forecasting.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REGRESSION_PREDICTION_SYSTEM = """You are a regression to mean prediction specialist. Given a forecast, assess whether regression to the mean has been accounted for:

Key concepts:
- Regression to the mean: extreme values tend to be followed by less extreme ones
- Reversion: natural tendency toward average over time
- Luck vs skill: extreme outcomes often include luck that won't persist
- Sports illustrated jinx: recognition after peak performance
- Sophomore slump: regression after exceptional debut
- Treatment effects: improvement after extreme may be regression, not treatment
- Signal vs noise: extreme observations have more noise

When regression prediction failure IS present:
- Extreme performance expected to continue at same level
- Outlier treated as new baseline
- No acknowledgment that extreme values tend to revert
- "Hot streak" expected to persist indefinitely
- Exceptional result attributed entirely to skill/cause
- Prediction based on peak rather than average
- No regression toward mean in forecast

When regression prediction is adequate:
- Extreme values expected to partially revert
- Predictions anchored to long-term average with adjustment
- Luck component acknowledged in extreme outcomes
- Forecast includes regression toward mean
- Distinction made between sustainable and unsustainable performance
- Base rate incorporated alongside recent extreme
- Confidence intervals widen for extreme starting points

Output JSON with: failure_present (bool), severity (none/mild/moderate/severe), extreme_observation (what extreme is being extrapolated), expected_regression (how much reversion should be expected), prediction_made (what is being predicted), base_rate (what the average is), recommendation (regression_accounted/mild_extrapolation/significant_failure/major_outlier_extrapolation/predict_regression)."""

REGRESSION_PREDICTION_PROMPT = """Detect regression prediction failure:

Forecast: {forecast}
Recent performance: {performance}
Historical average: {average}
Variability: {variability}
Domain: {domain}
Context: {context}

Has regression to the mean been accounted for in this prediction? Return ONLY valid JSON."""


class RegressionPredictionService:
    """Detects failure to predict regression to the mean."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        forecast: str,
        *,
        performance: str = "",
        average: str = "",
        variability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regression prediction failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REGRESSION_PREDICTION_PROMPT.format(
                forecast=forecast,
                performance=performance or "Not specified",
                average=average or "Not specified",
                variability=variability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REGRESSION_PREDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "forecast": forecast[:200],
            "failure_present": data.get("failure_present", False),
            "severity": data.get("severity", ""),
            "extreme_observation": data.get("extreme_observation", ""),
            "expected_regression": data.get("expected_regression", ""),
            "base_rate": data.get("base_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMetaCalibrationNeglectService — Epistemic Meta Calibration Neglect Detection.

Detects calibration neglect — failing to track and improve one's prediction accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_META_CALIBRATION_NEGLECT_SYSTEM = """You are an epistemic meta calibration neglect specialist. Given absent accuracy tracking, assess prediction calibration failure:

Key concepts:
- Calibration neglect: failing to track and improve prediction accuracy
- Accuracy tracking absence: not measuring prediction outcomes
- Feedback avoidance: avoiding evidence about forecast quality
- Base rate neglect: ignoring reference class frequencies
- Overconfidence persistence: confidence staying high despite errors

When calibration neglect IS present:
- Prediction accuracy is not tracked
- Feedback is avoided or discounted
- Base rates are ignored
- Overconfidence persists after misses
- Forecasting process does not improve from outcomes

When no calibration neglect:
- Predictions are logged and scored
- Feedback is sought and incorporated
- Base rates inform estimates
- Confidence changes after errors
- Forecasting process improves with evidence

Output JSON with: calibration_neglect_detected (bool), severity (none/mild/moderate/severe), feedback_avoidance (what feedback is avoided), base_rate_neglect (what base rates are ignored), overconfidence_persistence (where overconfidence persists), recommendation (no_calibration_neglect/mild_accuracy_tracking/significant_forecast_scoring/major_calibration_program/emergency_complete_prediction_audit)."""

EPISTEMIC_META_CALIBRATION_NEGLECT_PROMPT = """Detect epistemic meta calibration neglect:

Accuracy tracking absence: {accuracy_tracking_absence}
Feedback avoidance: {feedback_avoidance}
Base rate neglect: {base_rate_neglect}
Overconfidence persistence: {overconfidence_persistence}
Domain: {domain}
Context: {context}

Is prediction accuracy failing to be tracked and improved? Return ONLY valid JSON."""


class EpistemicMetaCalibrationNeglectService:
    """Detects calibration neglect — failure to track prediction accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        accuracy_tracking_absence: str,
        *,
        feedback_avoidance: str = "",
        base_rate_neglect: str = "",
        overconfidence_persistence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meta calibration neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_META_CALIBRATION_NEGLECT_PROMPT.format(
                accuracy_tracking_absence=accuracy_tracking_absence,
                feedback_avoidance=feedback_avoidance or "Not specified",
                base_rate_neglect=base_rate_neglect or "Not specified",
                overconfidence_persistence=overconfidence_persistence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_META_CALIBRATION_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "accuracy_tracking_absence": accuracy_tracking_absence[:200],
            "calibration_neglect_detected": data.get("calibration_neglect_detected", False),
            "severity": data.get("severity", ""),
            "feedback_avoidance": data.get("feedback_avoidance", ""),
            "base_rate_neglect": data.get("base_rate_neglect", ""),
            "overconfidence_persistence": data.get("overconfidence_persistence", ""),
            "recommendation": data.get("recommendation", ""),
        }

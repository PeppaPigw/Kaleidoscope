"""EpistemicPredictionOverconfidenceService — Epistemic Prediction Overconfidence Detection.

Detects epistemic prediction overconfidence — systematic overconfidence in prediction
accuracy, with confidence intervals too narrow and point estimates too precise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREDICTION_OVERCONFIDENCE_SYSTEM = """You are an epistemic prediction overconfidence specialist. Given prediction overconfidence, assess calibration failure:

Key concepts:
- Epistemic prediction overconfidence: confidence exceeding accuracy
- Narrow intervals: confidence intervals too tight for actual uncertainty
- False precision: point estimates implying more knowledge than exists
- Complexity underestimation: underestimating prediction difficulty
- Track record blindness: ignoring poor past prediction performance
- Domain difficulty denial: denying that some domains are inherently unpredictable
- Expertise overestimation: experts overestimating their predictive ability

When epistemic prediction overconfidence IS present:
- Confidence exceeding accuracy
- Intervals too narrow
- False precision in estimates
- Complexity underestimated
- Poor track record ignored
- Domain difficulty denied
- Expertise overestimated

When no prediction overconfidence:
- Confidence calibrated to accuracy
- Intervals appropriately wide
- Precision matched to knowledge
- Complexity acknowledged
- Track record incorporated
- Domain difficulty recognized
- Expertise limits acknowledged

Output JSON with: prediction_overconfidence_detected (bool), severity (none/mild/moderate/severe), narrow_intervals (what intervals too tight), false_precision (what precision unjustified), complexity_underestimation (what complexity underestimated), track_record_blindness (what track record ignored), recommendation (no_prediction_overconfidence/mild_interval_widening/significant_calibration_training/major_intensive_prediction_audit/emergency_complete_prediction_overconfidence)."""

EPISTEMIC_PREDICTION_OVERCONFIDENCE_PROMPT = """Detect epistemic prediction overconfidence:

Narrow intervals: {narrow_intervals}
False precision: {false_precision}
Complexity underestimation: {complexity_underestimation}
Track record blindness: {track_record_blindness}
Domain: {domain}
Context: {context}

Is there systematic overconfidence in prediction accuracy? Return ONLY valid JSON."""


class EpistemicPredictionOverconfidenceService:
    """Detects epistemic prediction overconfidence — calibration failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrow_intervals: str,
        *,
        false_precision: str = "",
        complexity_underestimation: str = "",
        track_record_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prediction overconfidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREDICTION_OVERCONFIDENCE_PROMPT.format(
                narrow_intervals=narrow_intervals,
                false_precision=false_precision or "Not specified",
                complexity_underestimation=complexity_underestimation or "Not specified",
                track_record_blindness=track_record_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREDICTION_OVERCONFIDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrow_intervals": narrow_intervals[:200],
            "prediction_overconfidence_detected": data.get("prediction_overconfidence_detected", False),
            "severity": data.get("severity", ""),
            "false_precision": data.get("false_precision", ""),
            "complexity_underestimation": data.get("complexity_underestimation", ""),
            "track_record_blindness": data.get("track_record_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }

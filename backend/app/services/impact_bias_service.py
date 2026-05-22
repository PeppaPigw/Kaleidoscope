"""ImpactBiasService — Impact Bias Detection.

Detects impact bias — overestimating the duration and intensity
of future emotional reactions to events. Gilbert et al. (1998).
People predict that positive events will make them happier for
longer, and negative events will make them sadder for longer,
than actually occurs. The psychological immune system is
consistently underestimated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IMPACT_BIAS_SYSTEM = """You are an impact bias specialist. Given a prediction about future emotional impact, assess whether the duration and intensity of emotional reactions are being overestimated:

Key concepts (Gilbert et al., 1998):
- Impact bias: overestimating emotional duration and intensity
- Durability bias: predicting feelings will last longer than they do
- Intensity bias: predicting feelings will be stronger than they are
- Psychological immune system: unconscious coping mechanisms
- Ordinization: extraordinary events become ordinary over time
- Hedonic adaptation: returning to baseline happiness
- Focalism: imagining only the focal event, not concurrent life

When impact bias IS present:
- "This will ruin everything" for a setback that will be adapted to
- "I'll be happy forever if..." for an achievement with temporary boost
- Decisions based on overestimated emotional consequences
- Catastrophizing future negative events
- Euphoric predictions about future positive events
- Ignoring evidence of past adaptation to similar events
- "I could never get over..." when people routinely do

When impact prediction IS calibrated:
- Predictions based on observed reactions to similar past events
- Accounting for adaptation and coping mechanisms
- Recognizing that life continues alongside any single event
- Distinguishing between events that do vs don't allow adaptation
- Calibrated by actual emotional tracking data

Output JSON with: impact_bias_present (bool), severity (none/mild/moderate/severe), prediction (what emotional impact is predicted), event (what event is being predicted about), overestimation (how is impact being overestimated), adaptation_evidence (evidence that adaptation will occur), duration_predicted (how long is the feeling predicted to last), likely_duration (how long will it likely actually last), recommendation (prediction_calibrated/mild_impact_overestimate/significant_impact_bias/major_durability_bias/account_for_psychological_immune_system)."""

IMPACT_BIAS_PROMPT = """Detect impact bias:

Prediction: {prediction}
Event: {event}
Past adaptation: {past}
Decision impact: {decision_impact}
Domain: {domain}
Context: {context}

Is the predicted emotional impact (duration/intensity) being overestimated? Return ONLY valid JSON."""


class ImpactBiasService:
    """Detects impact bias — overestimating duration/intensity of future emotional reactions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        event: str = "",
        past: str = "",
        decision_impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect impact bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IMPACT_BIAS_PROMPT.format(
                prediction=prediction,
                event=event or "Not specified",
                past=past or "Not specified",
                decision_impact=decision_impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IMPACT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "impact_bias_present": data.get("impact_bias_present", False),
            "severity": data.get("severity", ""),
            "overestimation": data.get("overestimation", ""),
            "adaptation_evidence": data.get("adaptation_evidence", ""),
            "duration_predicted": data.get("duration_predicted", ""),
            "likely_duration": data.get("likely_duration", ""),
            "event": data.get("event", ""),
            "recommendation": data.get("recommendation", ""),
        }

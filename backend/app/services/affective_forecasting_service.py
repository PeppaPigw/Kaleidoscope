"""AffectiveForecastingService — Affective Forecasting Error Detection.

Detects affective forecasting errors — mispredicting future
emotional states. Wilson & Gilbert (2003). People systematically
overestimate how good or bad future events will make them feel,
how long the feeling will last, and how much it will affect
their overall happiness. This leads to poor decisions optimizing
for predicted emotions that won't materialize as expected.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AFFECTIVE_FORECASTING_SYSTEM = """You are an affective forecasting specialist. Given a decision based on predicted emotional outcomes, assess whether affective forecasting errors are present:

Key concepts (Wilson & Gilbert, 2003):
- Affective forecasting: predicting future emotional states
- Impact bias: overestimating intensity and duration of reactions
- Immune neglect: forgetting psychological adaptation mechanisms
- Focalism: focusing on one event while ignoring other life factors
- Distinction bias: overweighting differences when comparing options
- Projection bias: assuming current feelings will persist
- Hot-cold empathy gap: inability to predict feelings in different states

When affective forecasting errors ARE present:
- "If I get this, I'll be happy forever"
- "If this happens, I'll never recover"
- Decisions based on predicted emotional states that won't materialize
- Ignoring psychological adaptation (hedonic treadmill)
- Overestimating how much a single outcome will affect overall wellbeing
- "I could never be happy if..." when evidence shows people adapt
- Choosing based on anticipated regret that's likely overestimated

When emotional prediction IS reasonable:
- Short-term emotional predictions (hours/days)
- Predictions about familiar emotional territory
- Situations where adaptation genuinely doesn't occur
- When the person has calibrated against past forecasting errors
- Predictions that account for adaptation and focalism

Output JSON with: forecasting_error_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), predicted_emotion (what emotional state is predicted), likely_actual (what will likely actually be felt), impact_bias (is intensity/duration overestimated), adaptation_ignored (is psychological adaptation being overlooked), focalism (is one factor being isolated from life context), recommendation (forecast_reasonable/mild_impact_bias/significant_forecasting_error/major_emotional_misprediction/account_for_adaptation)."""

AFFECTIVE_FORECASTING_PROMPT = """Detect affective forecasting error:

Decision: {decision}
Predicted feeling: {predicted}
Basis: {basis}
Adaptation history: {adaptation}
Domain: {domain}
Context: {context}

Is the decision based on mispredicted future emotional states? Return ONLY valid JSON."""


class AffectiveForecastingService:
    """Detects affective forecasting errors — mispredicting future emotional states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        predicted: str = "",
        basis: str = "",
        adaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect affective forecasting errors."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AFFECTIVE_FORECASTING_PROMPT.format(
                decision=decision,
                predicted=predicted or "Not specified",
                basis=basis or "Not specified",
                adaptation=adaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AFFECTIVE_FORECASTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "forecasting_error_present": data.get("forecasting_error_present", False),
            "severity": data.get("severity", ""),
            "predicted_emotion": data.get("predicted_emotion", ""),
            "likely_actual": data.get("likely_actual", ""),
            "impact_bias": data.get("impact_bias", ""),
            "adaptation_ignored": data.get("adaptation_ignored", ""),
            "focalism": data.get("focalism", ""),
            "recommendation": data.get("recommendation", ""),
        }

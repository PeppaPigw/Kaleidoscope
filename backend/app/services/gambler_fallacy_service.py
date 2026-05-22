"""GamblerFallacyService — Gambler's Fallacy Detection.

Detects the gambler's fallacy — the belief that past independent
random events affect future probabilities. "Red has come up 5
times, so black is due." Also detects the hot hand fallacy
(its inverse) and regression neglect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GAMBLER_SYSTEM = """You are a gambler's fallacy specialist. Given a prediction or expectation, assess whether the gambler's fallacy is distorting probability judgment:

Key concepts:
- Gambler's fallacy: believing past outcomes of independent events affect future probabilities
- Hot hand fallacy: believing a streak will continue when events are independent
- Law of small numbers: expecting small samples to be representative
- Regression neglect: failing to expect regression to the mean after extreme outcomes
- Independence: past coin flips don't affect future ones
- Representativeness heuristic: expecting sequences to "look random"

When the gambler's fallacy IS present:
- Expecting a reversal after a streak in independent events
- "It's due" reasoning with no causal mechanism
- Treating random variation as meaningful pattern
- Expecting small samples to balance out

When pattern-based reasoning IS valid:
- Events are NOT independent (e.g., team morale, momentum in some contexts)
- There's a causal mechanism for streaks or reversals
- The system has mean-reverting properties (not just statistical regression)
- Base rates are shifting due to real changes

Output JSON with: gambler_fallacy_present (bool), severity (none/mild/moderate/severe), prediction (what outcome is expected), reasoning (why they expect it), events_independent (bool — are the events actually independent?), causal_mechanism (is there a real mechanism, or just pattern-matching?), streak_length (how long the observed streak is), base_rate (what the actual probability is), hot_hand_variant (bool — expecting streak to continue rather than reverse?), regression_neglect (bool — failing to expect regression to mean?), law_of_small_numbers (bool — expecting small samples to be representative?), sample_size_adequate (bool), actual_probability (what the real probability is given independence), representativeness_heuristic (bool — expecting sequences to "look random"?), financial_risk (if applicable, what financial exposure this creates), recommendation (reasoning_valid/mild_pattern_bias/significant_gambler_fallacy/major_probability_error/events_not_independent_reasoning_may_be_valid)."""

GAMBLER_PROMPT = """Detect gambler's fallacy:

Prediction/Expectation: {prediction}
Past events: {past_events}
Reasoning given: {reasoning}
Event type: {event_type}
Domain: {domain}
Context: {context}

Is the gambler's fallacy distorting this prediction? Return ONLY valid JSON."""


class GamblerFallacyService:
    """Detects gambler's fallacy — misunderstanding independence in random events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        past_events: str = "",
        reasoning: str = "",
        event_type: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect gambler's fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GAMBLER_PROMPT.format(
                prediction=prediction,
                past_events=past_events or "Not specified",
                reasoning=reasoning or "Not specified",
                event_type=event_type or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GAMBLER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "gambler_fallacy_present": data.get("gambler_fallacy_present", False),
            "severity": data.get("severity", ""),
            "prediction_detail": data.get("prediction", ""),
            "reasoning_given": data.get("reasoning", ""),
            "events_independent": data.get("events_independent", True),
            "causal_mechanism": data.get("causal_mechanism", ""),
            "streak_length": data.get("streak_length", ""),
            "base_rate": data.get("base_rate", ""),
            "hot_hand_variant": data.get("hot_hand_variant", False),
            "regression_neglect": data.get("regression_neglect", False),
            "law_of_small_numbers": data.get("law_of_small_numbers", False),
            "sample_size_adequate": data.get("sample_size_adequate", False),
            "actual_probability": data.get("actual_probability", ""),
            "representativeness_heuristic": data.get("representativeness_heuristic", False),
            "financial_risk": data.get("financial_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }

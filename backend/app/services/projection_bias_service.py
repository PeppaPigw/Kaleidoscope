"""ProjectionBiasService — Projection Bias Detection.

Detects projection bias — assuming future preferences will match
current preferences. Loewenstein, O'Donoghue & Rabin (2003).
Shopping hungry makes you buy too much food. Planning vacation
activities while excited leads to over-scheduling. Current
emotional/physical state is projected onto future self.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROJECTION_SYSTEM = """You are a projection bias specialist. Given a prediction about future preferences, assess whether current state is being inappropriately projected onto the future:

Key concepts (Loewenstein, O'Donoghue & Rabin, 2003):
- Projection bias: assuming future preferences will match current state
- Hot state projection: current emotions/drives projected onto future calm self
- Cold state projection: current calm state projected onto future emotional self
- Durability bias overlap: overestimating how long current feelings will last
- Impact bias overlap: overestimating future emotional impact
- State-dependent preferences: preferences that change with physical/emotional state

When projection bias IS present:
- Making long-term decisions based on temporary emotional states
- Shopping while hungry, tired, excited, or emotional
- Assuming current enthusiasm will persist indefinitely
- Planning based on how you feel now rather than how you'll feel then
- Underestimating how much preferences change with context
- "I'll always want this" based on current desire

When current-state planning IS appropriate:
- Preferences are genuinely stable (core values, long-held interests)
- The decision is short-term enough that state won't change
- Past experience confirms preference stability in this domain
- The person has explicitly accounted for state changes
- Multiple states have been considered in the decision

Output JSON with: projection_bias_present (bool), severity (none/mild/moderate/severe), prediction (what future preference is being assumed), current_state (what current state is driving the prediction), state_type (emotional/physical/motivational/social), likely_future_state (what state will likely exist when the prediction matters), state_stability (how stable is this preference historically?), decision_horizon (how far in the future does this matter?), reversibility (can the decision be undone if preferences change?), past_pattern (has this person's preference changed before in similar situations?), hot_cold_direction (projecting hot→cold or cold→hot?), adaptation_neglect (bool — ignoring that feelings will change?), recommendation (projection_appropriate/mild_projection/significant_projection_bias/major_projection_bias/account_for_state_change)."""

PROJECTION_PROMPT = """Detect projection bias:

Prediction: {prediction}
Current state: {current_state}
Decision: {decision}
Time horizon: {horizon}
Domain: {domain}
Context: {context}

Is the current state being inappropriately projected onto future preferences? Return ONLY valid JSON."""


class ProjectionBiasService:
    """Detects projection bias — projecting current preferences onto future self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        current_state: str = "",
        decision: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect projection bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROJECTION_PROMPT.format(
                prediction=prediction,
                current_state=current_state or "Not specified",
                decision=decision or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "projection_bias_present": data.get("projection_bias_present", False),
            "severity": data.get("severity", ""),
            "current_state": data.get("current_state", ""),
            "state_type": data.get("state_type", ""),
            "likely_future_state": data.get("likely_future_state", ""),
            "state_stability": data.get("state_stability", ""),
            "decision_horizon": data.get("decision_horizon", ""),
            "reversibility": data.get("reversibility", ""),
            "past_pattern": data.get("past_pattern", ""),
            "hot_cold_direction": data.get("hot_cold_direction", ""),
            "adaptation_neglect": data.get("adaptation_neglect", False),
            "recommendation": data.get("recommendation", ""),
        }

"""EmpathyGapService — Hot-Cold Empathy Gap Detection.

Detects the hot-cold empathy gap — inability to predict how
you'll behave in a different emotional/physical state.
Loewenstein (2005). When calm, you underestimate how you'll
act when angry. When full, you underestimate future hunger.
Systematic failure to empathize with your own future self
in a different state.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EMPATHY_GAP_SYSTEM = """You are a hot-cold empathy gap specialist. Given a prediction about behavior in a different state, assess whether the empathy gap is causing miscalibration:

Key concepts (Loewenstein, 2005):
- Hot-cold empathy gap: inability to predict behavior in a different emotional state
- Hot state: high arousal — anger, hunger, pain, sexual arousal, craving
- Cold state: low arousal — calm, satiated, comfortable, rational
- Cold-to-hot: underestimating how drives will affect behavior when aroused
- Hot-to-cold: overestimating how much current drives will persist
- Visceral factors: bodily states that powerfully influence behavior but are hard to predict

When the empathy gap IS present:
- Making commitments while calm that will be tested under stress
- Underestimating how hunger/anger/fatigue will affect decisions
- "I would never do that" about behavior common under strong emotion
- Designing systems assuming rational actors when users will be emotional
- Planning without accounting for how state changes affect willpower
- Judging others' emotional behavior from a calm perspective

When state prediction IS accurate:
- The person has extensive experience with the state transition
- Explicit strategies are in place for state-dependent behavior
- The prediction accounts for known state effects
- Past behavior in similar states has been reviewed
- Environmental design compensates for state changes

Output JSON with: empathy_gap_present (bool), severity (none/mild/moderate/severe), current_state (hot or cold), predicted_state (what state will exist during the relevant behavior), prediction (what behavior is being predicted), likely_actual_behavior (what will likely happen in the other state), gap_direction (cold_to_hot/hot_to_cold), visceral_factor (what drive or emotion is involved), experience_with_state (has the person been in this state before?), commitment_at_risk (what commitment might break under state change?), environmental_design (are there safeguards for state changes?), self_knowledge (how well does the person know their state-dependent behavior?), recommendation (prediction_calibrated/mild_empathy_gap/significant_empathy_gap/major_empathy_gap/design_for_state_change)."""

EMPATHY_GAP_PROMPT = """Detect hot-cold empathy gap:

Prediction: {prediction}
Current state: {current_state}
Target state: {target_state}
Commitment: {commitment}
Domain: {domain}
Context: {context}

Is the empathy gap causing miscalibration about behavior in a different state? Return ONLY valid JSON."""


class EmpathyGapService:
    """Detects hot-cold empathy gap — failure to predict state-dependent behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        current_state: str = "",
        target_state: str = "",
        commitment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect empathy gap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EMPATHY_GAP_PROMPT.format(
                prediction=prediction,
                current_state=current_state or "Not specified",
                target_state=target_state or "Not specified",
                commitment=commitment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EMPATHY_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "empathy_gap_present": data.get("empathy_gap_present", False),
            "severity": data.get("severity", ""),
            "current_state": data.get("current_state", ""),
            "predicted_state": data.get("predicted_state", ""),
            "likely_actual_behavior": data.get("likely_actual_behavior", ""),
            "gap_direction": data.get("gap_direction", ""),
            "visceral_factor": data.get("visceral_factor", ""),
            "experience_with_state": data.get("experience_with_state", ""),
            "commitment_at_risk": data.get("commitment_at_risk", ""),
            "environmental_design": data.get("environmental_design", ""),
            "self_knowledge": data.get("self_knowledge", ""),
            "recommendation": data.get("recommendation", ""),
        }

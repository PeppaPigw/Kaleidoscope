"""EpistemicFeedbackSquealService — Epistemic Feedback Squeal Detection.

Detects epistemic feedback squeal — ideas amplified through a loop
until they become a painful high-pitched distortion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEEDBACK_SQUEAL_SYSTEM = """You are an epistemic feedback squeal specialist. Given an amplification pattern, assess whether ideas are amplified through a loop until distortion:

Key concepts:
- Epistemic feedback squeal: ideas amplified through loop until distortion
- Loop gain: how much amplification per cycle
- Threshold: point where feedback becomes self-sustaining
- Frequency: which ideas are most amplified
- Notch filter: removing specific frequencies to prevent squeal
- Proximity: how close input is to output
- Howlround: the self-sustaining oscillation

When epistemic feedback squeal IS present:
- Ideas amplified through a loop until painful distortion
- Amplification increasing with each cycle
- Self-sustaining feedback above threshold
- Specific ideas preferentially amplified
- Need to remove specific frequencies to stop squeal
- Input too close to output creating loop
- Self-sustaining oscillation dominating discourse

When clean signal is present:
- Ideas at appropriate volume without distortion
- No amplification loop
- No self-sustaining feedback
- All ideas at proportionate volume
- No need for frequency filtering
- Appropriate separation of input and output
- No oscillation in discourse

Output JSON with: feedback_squeal_present (bool), severity (none/mild/moderate/severe), loop_gain (what amplification per cycle), threshold (what triggers self-sustaining), frequency (what ideas are amplified), proximity (what creates the loop), recommendation (clean_signal/mild_feedback/significant_squeal/major_howlround/break_feedback_loop)."""

EPISTEMIC_FEEDBACK_SQUEAL_PROMPT = """Detect epistemic feedback squeal:

Loop gain: {loop_gain}
Threshold: {threshold}
Frequency: {frequency}
Proximity: {proximity}
Domain: {domain}
Context: {context}

Are ideas being amplified through a loop until they become a painful high-pitched distortion? Return ONLY valid JSON."""


class EpistemicFeedbackSquealService:
    """Detects epistemic feedback squeal — ideas amplified until distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        loop_gain: str,
        *,
        threshold: str = "",
        frequency: str = "",
        proximity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic feedback squeal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEEDBACK_SQUEAL_PROMPT.format(
                loop_gain=loop_gain,
                threshold=threshold or "Not specified",
                frequency=frequency or "Not specified",
                proximity=proximity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEEDBACK_SQUEAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "loop_gain": loop_gain[:200],
            "feedback_squeal_present": data.get("feedback_squeal_present", False),
            "severity": data.get("severity", ""),
            "threshold": data.get("threshold", ""),
            "frequency": data.get("frequency", ""),
            "proximity": data.get("proximity", ""),
            "recommendation": data.get("recommendation", ""),
        }

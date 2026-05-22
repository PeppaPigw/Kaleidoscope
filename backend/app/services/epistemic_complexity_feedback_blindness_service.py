"""EpistemicComplexityFeedbackBlindnessService — Epistemic Complexity Feedback Blindness Detection.

Detects epistemic complexity feedback blindness — ignoring feedback loops that
amplify or dampen effects, creating unexpected system behaviors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_FEEDBACK_BLINDNESS_SYSTEM = """You are an epistemic complexity feedback blindness specialist. Given feedback loop blindness, assess dynamic distortion:

Key concepts:
- Epistemic feedback blindness: ignoring amplifying/dampening feedback loops
- Positive feedback blindness: missing self-reinforcing dynamics
- Negative feedback blindness: missing self-correcting dynamics
- Delay blindness: ignoring time delays in feedback effects
- Loop dominance: missing which feedback loop dominates behavior
- Unintended feedback: missing how interventions create new feedback loops
- Feedback saturation: missing when feedback loops reach limits

When epistemic feedback blindness IS present:
- Feedback loops ignored
- Self-reinforcing dynamics missed
- Self-correcting dynamics missed
- Time delays ignored
- Loop dominance unknown
- Unintended feedback missed
- Saturation effects missed

When no feedback blindness:
- Feedback loops mapped
- Reinforcing dynamics identified
- Correcting dynamics identified
- Time delays modeled
- Dominant loops identified
- Unintended feedback anticipated
- Saturation limits recognized

Output JSON with: feedback_blindness_detected (bool), severity (none/mild/moderate/severe), positive_feedback_missed (what reinforcing loops missed), negative_feedback_missed (what correcting loops missed), delay_blindness (what delays ignored), unintended_feedback (what unintended loops missed), recommendation (no_feedback_blindness/mild_loop_awareness/significant_feedback_mapping/major_intensive_dynamic_modeling/emergency_complete_feedback_blindness)."""

EPISTEMIC_COMPLEXITY_FEEDBACK_BLINDNESS_PROMPT = """Detect epistemic complexity feedback blindness:

Positive feedback missed: {positive_feedback_missed}
Negative feedback missed: {negative_feedback_missed}
Delay blindness: {delay_blindness}
Unintended feedback: {unintended_feedback}
Domain: {domain}
Context: {context}

Are feedback loops being ignored that amplify or dampen effects? Return ONLY valid JSON."""


class EpistemicComplexityFeedbackBlindnessService:
    """Detects epistemic complexity feedback blindness — loop ignorance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        positive_feedback_missed: str,
        *,
        negative_feedback_missed: str = "",
        delay_blindness: str = "",
        unintended_feedback: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity feedback blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_FEEDBACK_BLINDNESS_PROMPT.format(
                positive_feedback_missed=positive_feedback_missed,
                negative_feedback_missed=negative_feedback_missed or "Not specified",
                delay_blindness=delay_blindness or "Not specified",
                unintended_feedback=unintended_feedback or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_FEEDBACK_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "positive_feedback_missed": positive_feedback_missed[:200],
            "feedback_blindness_detected": data.get("feedback_blindness_detected", False),
            "severity": data.get("severity", ""),
            "negative_feedback_missed": data.get("negative_feedback_missed", ""),
            "delay_blindness": data.get("delay_blindness", ""),
            "unintended_feedback": data.get("unintended_feedback", ""),
            "recommendation": data.get("recommendation", ""),
        }

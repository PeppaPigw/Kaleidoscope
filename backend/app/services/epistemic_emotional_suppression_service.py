"""EpistemicEmotionalSuppressionService — Epistemic Emotional Suppression Detection.

Detects epistemic emotional suppression — suppressing emotions that carry
important epistemic information about values and priorities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_SUPPRESSION_SYSTEM = """You are an epistemic emotional suppression specialist. Given suppressing epistemically informative emotions, assess emotional suppression:

Key concepts:
- Epistemic emotional suppression: suppressing emotions carrying epistemic information
- Gut feeling dismissal: dismissing gut feelings that carry information
- Intuition suppression: suppressing intuitions that signal something
- Discomfort avoidance: avoiding discomfort that signals problems
- Value signal blocking: blocking emotional signals about values
- Alarm suppression: suppressing emotional alarms
- Felt sense denial: denying felt sense of wrongness

When epistemic emotional suppression IS present:
- Suppressing informative emotions
- Dismissing gut feelings
- Suppressing intuitions
- Avoiding informative discomfort
- Blocking value signals
- Suppressing alarms
- Denying felt sense

When no emotional suppression:
- Attending to emotions as information
- Listening to gut feelings
- Honoring intuitions
- Engaging with discomfort
- Receiving value signals
- Heeding alarms
- Trusting felt sense

Output JSON with: emotional_suppression_detected (bool), severity (none/mild/moderate/severe), gut_feeling_dismissal (what gut feelings dismissed), intuition_suppression (what intuitions suppressed), discomfort_avoidance (what discomfort avoided), alarm_suppression (what alarms suppressed), recommendation (no_emotional_suppression/mild_listening_practice/significant_emotion_integration/major_intensive_felt_sense_recovery/emergency_complete_emotional_suppression)."""

EPISTEMIC_EMOTIONAL_SUPPRESSION_PROMPT = """Detect epistemic emotional suppression:

Gut feeling dismissal: {gut_feeling_dismissal}
Intuition suppression: {intuition_suppression}
Discomfort avoidance: {discomfort_avoidance}
Alarm suppression: {alarm_suppression}
Domain: {domain}
Context: {context}

Are emotions carrying important epistemic information being suppressed? Return ONLY valid JSON."""


class EpistemicEmotionalSuppressionService:
    """Detects epistemic emotional suppression — suppressing informative emotions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gut_feeling_dismissal: str,
        *,
        intuition_suppression: str = "",
        discomfort_avoidance: str = "",
        alarm_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_SUPPRESSION_PROMPT.format(
                gut_feeling_dismissal=gut_feeling_dismissal,
                intuition_suppression=intuition_suppression or "Not specified",
                discomfort_avoidance=discomfort_avoidance or "Not specified",
                alarm_suppression=alarm_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gut_feeling_dismissal": gut_feeling_dismissal[:200],
            "emotional_suppression_detected": data.get("emotional_suppression_detected", False),
            "severity": data.get("severity", ""),
            "intuition_suppression": data.get("intuition_suppression", ""),
            "discomfort_avoidance": data.get("discomfort_avoidance", ""),
            "alarm_suppression": data.get("alarm_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }

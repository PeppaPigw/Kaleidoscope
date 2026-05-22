"""EpistemicEmotionalDysregulationService — Epistemic Emotional Dysregulation Detection.

Detects epistemic emotional dysregulation — inability to regulate emotional
responses to intellectual content, ideas, or disagreements.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_DYSREGULATION_SYSTEM = """You are an epistemic emotional dysregulation specialist. Given inability to regulate intellectual emotions, assess dysregulation:

Key concepts:
- Epistemic emotional dysregulation: can't regulate intellectual feelings
- Intensity mismatch: emotional response far exceeds intellectual trigger
- Rapid escalation: going from calm to overwhelmed instantly
- Slow return: taking very long to recover from intellectual upset
- Flooding: completely overwhelmed by intellectual emotion
- Reactivity: hair-trigger emotional responses to ideas
- Mood dependence: intellectual capacity varies with emotional state

When epistemic emotional dysregulation IS present:
- Can't regulate intellectual feelings
- Response far exceeds trigger
- Calm to overwhelmed instantly
- Very long recovery
- Completely overwhelmed
- Hair-trigger responses
- Capacity varies with mood

When no emotional dysregulation:
- Regulated intellectual emotions
- Proportionate responses
- Gradual escalation
- Quick recovery
- Manageable feelings
- Measured responses
- Stable capacity

Output JSON with: emotional_dysregulation_detected (bool), severity (none/mild/moderate/severe), intensity_mismatch (what exceeding), escalation_pattern (what rapid), flooding_level (what overwhelming), mood_dependence (what varying), recommendation (no_dysregulation/mild_regulation_skills/significant_emotion_management/major_intensive_regulation_therapy/emergency_severe_flooding)."""

EPISTEMIC_EMOTIONAL_DYSREGULATION_PROMPT = """Detect epistemic emotional dysregulation:

Intensity mismatch: {intensity_mismatch}
Escalation pattern: {escalation_pattern}
Flooding level: {flooding_level}
Mood dependence: {mood_dependence}
Domain: {domain}
Context: {context}

Is there inability to regulate emotional responses to intellectual content? Return ONLY valid JSON."""


class EpistemicEmotionalDysregulationService:
    """Detects epistemic emotional dysregulation — can't regulate intellectual emotions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intensity_mismatch: str,
        *,
        escalation_pattern: str = "",
        flooding_level: str = "",
        mood_dependence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional dysregulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_DYSREGULATION_PROMPT.format(
                intensity_mismatch=intensity_mismatch,
                escalation_pattern=escalation_pattern or "Not specified",
                flooding_level=flooding_level or "Not specified",
                mood_dependence=mood_dependence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_DYSREGULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intensity_mismatch": intensity_mismatch[:200],
            "emotional_dysregulation_detected": data.get("emotional_dysregulation_detected", False),
            "severity": data.get("severity", ""),
            "escalation_pattern": data.get("escalation_pattern", ""),
            "flooding_level": data.get("flooding_level", ""),
            "mood_dependence": data.get("mood_dependence", ""),
            "recommendation": data.get("recommendation", ""),
        }

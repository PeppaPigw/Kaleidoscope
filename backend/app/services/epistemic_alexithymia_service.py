"""EpistemicAlexithymiaService — Epistemic Alexithymia Detection.

Detects epistemic alexithymia — inability to identify, describe, or
differentiate intellectual emotions and feelings about ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ALEXITHYMIA_SYSTEM = """You are an epistemic alexithymia specialist. Given inability to identify intellectual emotions, assess alexithymia:

Key concepts:
- Epistemic alexithymia: can't identify feelings about ideas
- Emotion blindness: not knowing what one feels intellectually
- Description deficit: unable to put intellectual feelings into words
- Differentiation failure: all intellectual feelings feel the same
- External orientation: focused on facts not feelings about facts
- Fantasy deficit: impoverished intellectual imagination
- Concrete thinking: unable to symbolize intellectual experience

When epistemic alexithymia IS present:
- Can't identify feelings about ideas
- Not knowing what feeling
- Unable to describe feelings
- All feelings feel same
- Focused on facts only
- Impoverished imagination
- Unable to symbolize

When no alexithymia:
- Clear feelings about ideas
- Knowing what feeling
- Describing feelings easily
- Differentiated emotions
- Balanced facts and feelings
- Rich imagination
- Symbolic capacity

Output JSON with: alexithymia_detected (bool), severity (none/mild/moderate/severe), emotion_blindness (what not knowing), description_deficit (what can't describe), differentiation_failure (what all same), concrete_thinking (what can't symbolize), recommendation (no_alexithymia/mild_emotion_labeling/significant_affect_education/major_intensive_alexithymia_therapy/emergency_severe_disconnection)."""

EPISTEMIC_ALEXITHYMIA_PROMPT = """Detect epistemic alexithymia:

Emotion blindness: {emotion_blindness}
Description deficit: {description_deficit}
Differentiation failure: {differentiation_failure}
Concrete thinking: {concrete_thinking}
Domain: {domain}
Context: {context}

Is there inability to identify or describe intellectual emotions? Return ONLY valid JSON."""


class EpistemicAlexithymiaService:
    """Detects epistemic alexithymia — can't identify intellectual emotions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        emotion_blindness: str,
        *,
        description_deficit: str = "",
        differentiation_failure: str = "",
        concrete_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic alexithymia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ALEXITHYMIA_PROMPT.format(
                emotion_blindness=emotion_blindness,
                description_deficit=description_deficit or "Not specified",
                differentiation_failure=differentiation_failure or "Not specified",
                concrete_thinking=concrete_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ALEXITHYMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "emotion_blindness": emotion_blindness[:200],
            "alexithymia_detected": data.get("alexithymia_detected", False),
            "severity": data.get("severity", ""),
            "description_deficit": data.get("description_deficit", ""),
            "differentiation_failure": data.get("differentiation_failure", ""),
            "concrete_thinking": data.get("concrete_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }

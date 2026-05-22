"""EpistemicEmbodimentConfusionService — Epistemic Embodiment Confusion Detection.

Detects epistemic embodiment confusion — confusing bodily states with
epistemic states, mistaking physical for intellectual.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIMENT_CONFUSION_SYSTEM = """You are an epistemic embodiment confusion specialist. Given confusing bodily states with epistemic states, assess embodiment confusion:

Key concepts:
- Epistemic embodiment confusion: confusing bodily states with epistemic states
- Hunger as doubt: mistaking hunger for intellectual doubt
- Fatigue as confusion: mistaking fatigue for genuine confusion
- Arousal as insight: mistaking arousal for intellectual insight
- Comfort as certainty: mistaking physical comfort for epistemic certainty
- Pain as wrongness: mistaking pain for being wrong
- Energy as truth: mistaking high energy for being right

When epistemic embodiment confusion IS present:
- Bodily states confused with epistemic
- Hunger mistaken for doubt
- Fatigue mistaken for confusion
- Arousal mistaken for insight
- Comfort mistaken for certainty
- Pain mistaken for wrongness
- Energy mistaken for truth

When no embodiment confusion:
- Bodily and epistemic states distinguished
- Hunger recognized as hunger
- Fatigue recognized as fatigue
- Arousal recognized as arousal
- Comfort separate from certainty
- Pain separate from wrongness
- Energy separate from truth

Output JSON with: embodiment_confusion_detected (bool), severity (none/mild/moderate/severe), fatigue_as_confusion (what fatigue mistaken for confusion about), comfort_as_certainty (what comfort mistaken for certainty about), arousal_as_insight (what arousal mistaken for insight about), energy_as_truth (what energy mistaken for truth about), recommendation (no_embodiment_confusion/mild_state_distinction/significant_body_mind_separation/major_intensive_state_literacy/emergency_complete_embodiment_confusion)."""

EPISTEMIC_EMBODIMENT_CONFUSION_PROMPT = """Detect epistemic embodiment confusion:

Fatigue as confusion: {fatigue_as_confusion}
Comfort as certainty: {comfort_as_certainty}
Arousal as insight: {arousal_as_insight}
Energy as truth: {energy_as_truth}
Domain: {domain}
Context: {context}

Are bodily states being confused with epistemic states? Return ONLY valid JSON."""


class EpistemicEmbodimentConfusionService:
    """Detects epistemic embodiment confusion — confusing body with epistemic states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fatigue_as_confusion: str,
        *,
        comfort_as_certainty: str = "",
        arousal_as_insight: str = "",
        energy_as_truth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodiment confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIMENT_CONFUSION_PROMPT.format(
                fatigue_as_confusion=fatigue_as_confusion,
                comfort_as_certainty=comfort_as_certainty or "Not specified",
                arousal_as_insight=arousal_as_insight or "Not specified",
                energy_as_truth=energy_as_truth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIMENT_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fatigue_as_confusion": fatigue_as_confusion[:200],
            "embodiment_confusion_detected": data.get("embodiment_confusion_detected", False),
            "severity": data.get("severity", ""),
            "comfort_as_certainty": data.get("comfort_as_certainty", ""),
            "arousal_as_insight": data.get("arousal_as_insight", ""),
            "energy_as_truth": data.get("energy_as_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }

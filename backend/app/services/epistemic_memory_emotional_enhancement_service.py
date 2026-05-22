"""EpistemicMemoryEmotionalEnhancementService — Epistemic Memory Emotional Enhancement Detection.

Detects epistemic memory emotional enhancement — emotional events remembered
with false vividness and fabricated details due to emotional intensity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_EMOTIONAL_ENHANCEMENT_SYSTEM = """You are an epistemic memory emotional enhancement specialist. Given emotional memory enhancement, assess false vividness:

Key concepts:
- Epistemic memory emotional enhancement: emotional intensity creating false detail
- Flashbulb memory illusion: vivid emotional memories that are inaccurate
- Emotional detail fabrication: fabricating details for emotionally charged events
- Confidence-accuracy dissociation: high confidence in inaccurate emotional memories
- Mood-congruent recall: current mood biasing what is remembered
- Emotional rehearsal distortion: repeated emotional retelling distorting memory
- Trauma memory distortion: traumatic intensity creating both gaps and false details

When epistemic memory emotional enhancement IS present:
- Emotional intensity creating false detail
- Flashbulb memories inaccurate
- Details fabricated for emotional events
- Confidence dissociated from accuracy
- Mood biasing recall
- Emotional rehearsal distorting
- Trauma creating false details

When no emotional enhancement:
- Emotional memories acknowledged as potentially distorted
- Vividness not equated with accuracy
- Details verified independently
- Confidence calibrated
- Mood effects acknowledged
- Rehearsal effects considered
- Trauma effects recognized

Output JSON with: emotional_enhancement_detected (bool), severity (none/mild/moderate/severe), flashbulb_illusion (what flashbulb illusions), detail_fabrication (what details fabricated), confidence_accuracy_gap (what confidence-accuracy gaps), mood_congruent_recall (what mood-congruent recall), recommendation (no_emotional_enhancement/mild_vividness_skepticism/significant_independent_verification/major_intensive_memory_audit/emergency_complete_emotional_enhancement)."""

EPISTEMIC_MEMORY_EMOTIONAL_ENHANCEMENT_PROMPT = """Detect epistemic memory emotional enhancement:

Flashbulb illusion: {flashbulb_illusion}
Detail fabrication: {detail_fabrication}
Confidence accuracy gap: {confidence_accuracy_gap}
Mood congruent recall: {mood_congruent_recall}
Domain: {domain}
Context: {context}

Are emotional events being remembered with false vividness and fabricated details? Return ONLY valid JSON."""


class EpistemicMemoryEmotionalEnhancementService:
    """Detects epistemic memory emotional enhancement — false vividness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flashbulb_illusion: str,
        *,
        detail_fabrication: str = "",
        confidence_accuracy_gap: str = "",
        mood_congruent_recall: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory emotional enhancement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_EMOTIONAL_ENHANCEMENT_PROMPT.format(
                flashbulb_illusion=flashbulb_illusion,
                detail_fabrication=detail_fabrication or "Not specified",
                confidence_accuracy_gap=confidence_accuracy_gap or "Not specified",
                mood_congruent_recall=mood_congruent_recall or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_EMOTIONAL_ENHANCEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flashbulb_illusion": flashbulb_illusion[:200],
            "emotional_enhancement_detected": data.get("emotional_enhancement_detected", False),
            "severity": data.get("severity", ""),
            "detail_fabrication": data.get("detail_fabrication", ""),
            "confidence_accuracy_gap": data.get("confidence_accuracy_gap", ""),
            "mood_congruent_recall": data.get("mood_congruent_recall", ""),
            "recommendation": data.get("recommendation", ""),
        }

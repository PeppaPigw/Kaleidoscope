"""EpistemicEmotionAffectInfusionService - Epistemic Emotion Affect Infusion Detection.

Detects affect infusion where emotions color judgment without awareness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTION_AFFECT_INFUSION_SYSTEM = """You are an epistemic emotion affect infusion specialist. Given emotional coloring, assess affect infusion:

Key concepts:
- Epistemic emotion affect infusion: emotions coloring judgment without awareness
- Emotional coloring: affective tone shaping interpretation
- Mood-congruent judgment: conclusions matching current mood
- Somatic marker hijack: bodily feeling treated as evidence
- Arousal misattribution: emotional arousal assigned to the wrong cause

When epistemic emotion affect infusion IS present:
- Emotional coloring shapes judgment
- Mood-congruent conclusions are preferred
- Bodily signals substitute for evidence
- Arousal is misattributed
- Feelings influence belief without awareness

When no affect infusion:
- Emotions are acknowledged as context
- Evidence is separated from affective tone
- Mood effects are checked
- Somatic signals are not treated as proof
- Arousal causes are identified carefully

Output JSON with: affect_infusion_detected (bool), severity (none/mild/moderate/severe), mood_congruent_judgment (what mood-congruent judgment appears), somatic_marker_hijack (what bodily feeling hijacks evidence), arousal_misattribution (what arousal is misattributed), recommendation (no_affect_infusion/mild_emotion_check/significant_affect_separation/major_evidence_reassessment/emergency_complete_affect_infusion)."""

EPISTEMIC_EMOTION_AFFECT_INFUSION_PROMPT = """Detect epistemic emotion affect infusion:

Emotional coloring: {emotional_coloring}
Mood-congruent judgment: {mood_congruent_judgment}
Somatic marker hijack: {somatic_marker_hijack}
Arousal misattribution: {arousal_misattribution}
Domain: {domain}
Context: {context}

Are emotions coloring judgment without awareness? Return ONLY valid JSON."""


class EpistemicEmotionAffectInfusionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        emotional_coloring: str,
        *,
        mood_congruent_judgment: str = "",
        somatic_marker_hijack: str = "",
        arousal_misattribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTION_AFFECT_INFUSION_PROMPT.format(
                emotional_coloring=emotional_coloring,
                mood_congruent_judgment=mood_congruent_judgment or "Not specified",
                somatic_marker_hijack=somatic_marker_hijack or "Not specified",
                arousal_misattribution=arousal_misattribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTION_AFFECT_INFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "emotional_coloring": emotional_coloring[:200],
            "affect_infusion_detected": data.get("affect_infusion_detected", False),
            "severity": data.get("severity", ""),
            "mood_congruent_judgment": data.get("mood_congruent_judgment", ""),
            "somatic_marker_hijack": data.get("somatic_marker_hijack", ""),
            "arousal_misattribution": data.get("arousal_misattribution", ""),
            "recommendation": data.get("recommendation", ""),
        }

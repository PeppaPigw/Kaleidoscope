"""EpistemicEmotionNostalgiaDistortionService - Epistemic Emotion Nostalgia Distortion Detection.

Detects nostalgia distortion where positive emotional coloring of past distorts historical understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTION_NOSTALGIA_DISTORTION_SYSTEM = """You are an epistemic emotion nostalgia distortion specialist. Given past idealization, assess nostalgia distortion:

Key concepts:
- Epistemic emotion nostalgia distortion: positive emotional coloring of the past distorting historical understanding
- Past idealization: remembering the past as better than it was
- Selective memory: preserving positive details while dropping negative details
- Golden age myth: treating an earlier period as superior by default
- Decline narrative: interpreting change as deterioration from an ideal past

When nostalgia distortion IS present:
- The past is idealized
- Memory is selective
- Golden age narratives dominate
- Decline is assumed
- Historical complexity is flattened by positive affect

When no nostalgia distortion:
- The past is evaluated with mixed evidence
- Memory selection is acknowledged
- Golden age claims are tested
- Decline narratives are contextualized
- Historical complexity is preserved

Output JSON with: nostalgia_distortion_detected (bool), severity (none/mild/moderate/severe), selective_memory (what memory selection appears), golden_age_myth (what golden age myth appears), decline_narrative (what decline narrative appears), recommendation (no_nostalgia_distortion/mild_memory_check/significant_historical_context/major_past_reassessment/emergency_complete_nostalgia_distortion)."""

EPISTEMIC_EMOTION_NOSTALGIA_DISTORTION_PROMPT = """Detect epistemic emotion nostalgia distortion:

Past idealization: {past_idealization}
Selective memory: {selective_memory}
Golden age myth: {golden_age_myth}
Decline narrative: {decline_narrative}
Domain: {domain}
Context: {context}

Is positive emotional coloring of the past distorting historical understanding? Return ONLY valid JSON."""


class EpistemicEmotionNostalgiaDistortionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        past_idealization: str,
        *,
        selective_memory: str = "",
        golden_age_myth: str = "",
        decline_narrative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTION_NOSTALGIA_DISTORTION_PROMPT.format(
                past_idealization=past_idealization,
                selective_memory=selective_memory or "Not specified",
                golden_age_myth=golden_age_myth or "Not specified",
                decline_narrative=decline_narrative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTION_NOSTALGIA_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "past_idealization": past_idealization[:200],
            "nostalgia_distortion_detected": data.get("nostalgia_distortion_detected", False),
            "severity": data.get("severity", ""),
            "selective_memory": data.get("selective_memory", ""),
            "golden_age_myth": data.get("golden_age_myth", ""),
            "decline_narrative": data.get("decline_narrative", ""),
            "recommendation": data.get("recommendation", ""),
        }

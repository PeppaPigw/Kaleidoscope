"""EpistemicCommunicationTonePolicingService - Tone Policing Detection.

Detects tone policing where content is dismissed based on delivery style.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_TONE_POLICING_SYSTEM = """You are an epistemic communication tone policing specialist. Given tone criticism, assess whether content is dismissed based on delivery style:

Key concepts:
- Tone policing: dismissing content based on how it is delivered rather than what is said
- Content dismissal: ignoring substance because of emotional expression
- Style over substance: prioritizing delivery over truth value
- Emotional invalidation: treating emotional expression as disqualifying

When tone policing IS present:
- Content dismissed due to delivery
- Substance ignored for style
- Emotional expression treated as disqualifying
- Respectability used as gatekeeping
- Valid points rejected for tone

When no tone policing:
- Delivery feedback separate from content engagement
- Substance addressed regardless of tone
- Emotional expression acknowledged
- Style suggestions offered constructively
- Content evaluated on merits

Output JSON with: tone_policing_detected (bool), severity (none/mild/moderate/severe), content_dismissed (what content dismissed), style_over_substance (what style prioritized), emotional_invalidation (what emotion invalidated), recommendation (no_tone_policing/mild_content_refocus/significant_substance_engagement/major_content_reconstruction/emergency_complete_tone_policing)."""

EPISTEMIC_COMMUNICATION_TONE_POLICING_PROMPT = """Detect epistemic communication tone policing:

Tone criticism: {tone_criticism}
Content dismissed: {content_dismissed}
Style over substance: {style_over_substance}
Emotional invalidation: {emotional_invalidation}
Domain: {domain}
Context: {context}

Is content being dismissed based on delivery style? Return ONLY valid JSON."""


class EpistemicCommunicationTonePolicingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tone_criticism: str,
        *,
        content_dismissed: str = "",
        style_over_substance: str = "",
        emotional_invalidation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_TONE_POLICING_PROMPT.format(
                tone_criticism=tone_criticism,
                content_dismissed=content_dismissed or "Not specified",
                style_over_substance=style_over_substance or "Not specified",
                emotional_invalidation=emotional_invalidation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_TONE_POLICING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tone_criticism": tone_criticism[:200],
            "tone_policing_detected": data.get("tone_policing_detected", False),
            "severity": data.get("severity", ""),
            "content_dismissed": data.get("content_dismissed", ""),
            "style_over_substance": data.get("style_over_substance", ""),
            "emotional_invalidation": data.get("emotional_invalidation", ""),
            "recommendation": data.get("recommendation", ""),
        }

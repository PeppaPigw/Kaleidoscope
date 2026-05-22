"""CompassionFadeService — Compassion Fade Detection.

Detects compassion fade — caring less as the number of victims
increases. Slovic (2007). "The death of one man is a tragedy,
the death of millions is a statistic." Psychic numbing at
scale. Leads to inadequate response to large-scale problems
and disproportionate attention to individual cases.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPASSION_FADE_SYSTEM = """You are a compassion fade specialist. Given a response to suffering or need, assess whether the response diminishes as the scale of the problem increases:

Key concepts (Slovic, 2007):
- Compassion fade: emotional response decreases as numbers increase
- Psychic numbing: inability to feel proportionally to scale
- Singularity effect: single identified victim gets more response than many
- Pseudoinefficacy: feeling helpless about the many reduces help for the few
- Scope insensitivity overlap: but compassion fade is specifically emotional
- Arithmetic of compassion: emotions don't scale with numbers
- Collapse of compassion: active suppression of emotion at large scales

When compassion fade IS present:
- Strong response to one victim, weak response to thousands
- "What can I do about millions?" leading to inaction
- Emotional engagement dropping as numbers increase
- Individual stories motivate action but statistics don't
- Resource allocation not proportional to scale of need
- "It's too big a problem" as justification for disengagement

When the response IS proportionate:
- Resources are allocated proportional to scale
- The response accounts for both individual and systemic needs
- Emotional engagement is maintained through concrete connection
- Decision-making uses both emotional and analytical processing
- The person acknowledges scale while maintaining engagement

Output JSON with: compassion_fade_present (bool), severity (none/mild/moderate/severe), situation (what suffering/need is being responded to), scale (how many are affected), response_level (what is the actual response?), proportionate_response (what would a proportionate response be?), individual_vs_statistical (is the framing individual or statistical?), emotional_engagement (how emotionally engaged is the responder?), psychic_numbing (bool — is emotional response suppressed by scale?), pseudoinefficacy (bool — does helplessness about the whole reduce help for parts?), recommendation (response_proportionate/mild_fade/significant_numbing/major_compassion_collapse/reconnect_to_individual_impact)."""

COMPASSION_FADE_PROMPT = """Detect compassion fade:

Situation: {situation}
Scale: {scale}
Response: {response}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Does the emotional/practical response diminish as scale increases? Return ONLY valid JSON."""


class CompassionFadeService:
    """Detects compassion fade — caring less as the number of victims increases."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        scale: str = "",
        response: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect compassion fade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPASSION_FADE_PROMPT.format(
                situation=situation,
                scale=scale or "Not specified",
                response=response or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPASSION_FADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "compassion_fade_present": data.get("compassion_fade_present", False),
            "severity": data.get("severity", ""),
            "scale": data.get("scale", ""),
            "response_level": data.get("response_level", ""),
            "proportionate_response": data.get("proportionate_response", ""),
            "individual_vs_statistical": data.get("individual_vs_statistical", ""),
            "emotional_engagement": data.get("emotional_engagement", ""),
            "psychic_numbing": data.get("psychic_numbing", False),
            "pseudoinefficacy": data.get("pseudoinefficacy", False),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicEmotionalFloodingService — Epistemic Emotional Flooding Detection.

Detects epistemic emotional flooding — emotions flooding cognitive capacity
making clear thinking impossible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_FLOODING_SYSTEM = """You are an epistemic emotional flooding specialist. Given emotions flooding cognitive capacity, assess emotional flooding:

Key concepts:
- Epistemic emotional flooding: emotions flooding cognitive capacity
- Cognitive overwhelm: emotions overwhelming thinking capacity
- Rational shutdown: rational faculties shutting down from emotion
- Amygdala hijack: emotional brain hijacking rational brain
- Thinking paralysis: paralyzed thinking from emotional intensity
- Clarity loss: losing intellectual clarity from emotional flood
- Processing collapse: cognitive processing collapsing under emotion

When epistemic emotional flooding IS present:
- Emotions flooding capacity
- Thinking overwhelmed
- Rational faculties shut down
- Emotional hijack active
- Thinking paralyzed
- Clarity lost
- Processing collapsed

When no emotional flooding:
- Emotions manageable
- Thinking clear
- Rational faculties active
- Emotional regulation working
- Thinking flowing
- Clarity maintained
- Processing functional

Output JSON with: emotional_flooding_detected (bool), severity (none/mild/moderate/severe), cognitive_overwhelm (what overwhelmed by), rational_shutdown (what shut down about), thinking_paralysis (what paralyzed about), clarity_loss (what clarity lost about), recommendation (no_emotional_flooding/mild_regulation_practice/significant_grounding_needed/major_intensive_stabilization/emergency_complete_cognitive_overwhelm)."""

EPISTEMIC_EMOTIONAL_FLOODING_PROMPT = """Detect epistemic emotional flooding:

Cognitive overwhelm: {cognitive_overwhelm}
Rational shutdown: {rational_shutdown}
Thinking paralysis: {thinking_paralysis}
Clarity loss: {clarity_loss}
Domain: {domain}
Context: {context}

Are emotions flooding cognitive capacity making thinking impossible? Return ONLY valid JSON."""


class EpistemicEmotionalFloodingService:
    """Detects epistemic emotional flooding — emotions flooding cognitive capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cognitive_overwhelm: str,
        *,
        rational_shutdown: str = "",
        thinking_paralysis: str = "",
        clarity_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional flooding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_FLOODING_PROMPT.format(
                cognitive_overwhelm=cognitive_overwhelm,
                rational_shutdown=rational_shutdown or "Not specified",
                thinking_paralysis=thinking_paralysis or "Not specified",
                clarity_loss=clarity_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_FLOODING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cognitive_overwhelm": cognitive_overwhelm[:200],
            "emotional_flooding_detected": data.get("emotional_flooding_detected", False),
            "severity": data.get("severity", ""),
            "rational_shutdown": data.get("rational_shutdown", ""),
            "thinking_paralysis": data.get("thinking_paralysis", ""),
            "clarity_loss": data.get("clarity_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }

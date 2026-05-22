"""EpistemicIntellectualServitudeService — Epistemic Intellectual Servitude Detection.

Detects epistemic intellectual servitude — intellectual servitude to
dominant thinkers, sacrificing own thought for their frameworks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_SERVITUDE_SYSTEM = """You are an epistemic intellectual servitude specialist. Given intellectual servitude to dominant thinkers, assess intellectual servitude:

Key concepts:
- Epistemic intellectual servitude: servitude to dominant thinkers
- Framework captivity: trapped in another's intellectual framework
- Thought colonization: own thinking colonized by authority
- Intellectual labor exploitation: doing thinking work for others' credit
- Disciple syndrome: existing only to serve master's ideas
- Voice suppression: suppressing own voice for authority's
- Intellectual feudalism: hierarchical knowledge relationships

When epistemic intellectual servitude IS present:
- Servitude to dominant thinkers
- Trapped in another's framework
- Thinking colonized by authority
- Doing work for others' credit
- Existing to serve master's ideas
- Suppressing own voice
- Hierarchical knowledge relationships

When no intellectual servitude:
- Intellectual freedom
- Choosing frameworks freely
- Own thinking autonomous
- Credited for own work
- Developing own ideas
- Expressing own voice
- Egalitarian knowledge relationships

Output JSON with: intellectual_servitude_detected (bool), severity (none/mild/moderate/severe), framework_captivity (what trapped in), thought_colonization (what colonized by), intellectual_labor_exploitation (what doing for others), voice_suppression (what suppressing), recommendation (no_intellectual_servitude/mild_autonomy_practice/significant_independence_building/major_intensive_liberation_work/emergency_complete_servitude)."""

EPISTEMIC_INTELLECTUAL_SERVITUDE_PROMPT = """Detect epistemic intellectual servitude:

Framework captivity: {framework_captivity}
Thought colonization: {thought_colonization}
Intellectual labor exploitation: {intellectual_labor_exploitation}
Voice suppression: {voice_suppression}
Domain: {domain}
Context: {context}

Is there intellectual servitude to dominant thinkers? Return ONLY valid JSON."""


class EpistemicIntellectualServitudeService:
    """Detects epistemic intellectual servitude — servitude to dominant thinkers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        framework_captivity: str,
        *,
        thought_colonization: str = "",
        intellectual_labor_exploitation: str = "",
        voice_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual servitude."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_SERVITUDE_PROMPT.format(
                framework_captivity=framework_captivity,
                thought_colonization=thought_colonization or "Not specified",
                intellectual_labor_exploitation=intellectual_labor_exploitation or "Not specified",
                voice_suppression=voice_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_SERVITUDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "framework_captivity": framework_captivity[:200],
            "intellectual_servitude_detected": data.get("intellectual_servitude_detected", False),
            "severity": data.get("severity", ""),
            "thought_colonization": data.get("thought_colonization", ""),
            "intellectual_labor_exploitation": data.get("intellectual_labor_exploitation", ""),
            "voice_suppression": data.get("voice_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicReplacementFearService — Epistemic Replacement Fear Detection.

Detects epistemic replacement fear — fear of being intellectually replaced
or made obsolete by others' contributions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REPLACEMENT_FEAR_SYSTEM = """You are an epistemic replacement fear specialist. Given fear of intellectual obsolescence, assess replacement fear:

Key concepts:
- Epistemic replacement fear: fear of being made obsolete
- Obsolescence anxiety: worry about becoming irrelevant
- Successor threat: seeing younger/newer thinkers as threats
- Legacy fragility: fear that contributions will be forgotten
- Relevance desperation: frantic efforts to stay current
- Displacement dread: fear of being pushed aside
- Generational anxiety: worry about being surpassed

When epistemic replacement fear IS present:
- Fear of being made obsolete
- Worry about irrelevance
- Seeing successors as threats
- Fear contributions forgotten
- Frantic efforts to stay current
- Fear of being pushed aside
- Worry about being surpassed

When no replacement fear:
- Secure in contributions
- Comfortable with evolution
- Mentoring successors
- Confident in legacy
- Natural growth
- Welcoming new voices
- Celebrating progress

Output JSON with: replacement_fear_detected (bool), severity (none/mild/moderate/severe), obsolescence_anxiety (what worrying about), successor_threat (what seeing as threat), legacy_fragility (what fearing forgotten), relevance_desperation (what frantically doing), recommendation (no_replacement_fear/mild_security_building/significant_legacy_work/major_intensive_acceptance_therapy/emergency_severe_obsolescence_panic)."""

EPISTEMIC_REPLACEMENT_FEAR_PROMPT = """Detect epistemic replacement fear:

Obsolescence anxiety: {obsolescence_anxiety}
Successor threat: {successor_threat}
Legacy fragility: {legacy_fragility}
Relevance desperation: {relevance_desperation}
Domain: {domain}
Context: {context}

Is there fear of being intellectually replaced or made obsolete? Return ONLY valid JSON."""


class EpistemicReplacementFearService:
    """Detects epistemic replacement fear — fear of being intellectually replaced."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        obsolescence_anxiety: str,
        *,
        successor_threat: str = "",
        legacy_fragility: str = "",
        relevance_desperation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic replacement fear."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REPLACEMENT_FEAR_PROMPT.format(
                obsolescence_anxiety=obsolescence_anxiety,
                successor_threat=successor_threat or "Not specified",
                legacy_fragility=legacy_fragility or "Not specified",
                relevance_desperation=relevance_desperation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REPLACEMENT_FEAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "obsolescence_anxiety": obsolescence_anxiety[:200],
            "replacement_fear_detected": data.get("replacement_fear_detected", False),
            "severity": data.get("severity", ""),
            "successor_threat": data.get("successor_threat", ""),
            "legacy_fragility": data.get("legacy_fragility", ""),
            "relevance_desperation": data.get("relevance_desperation", ""),
            "recommendation": data.get("recommendation", ""),
        }

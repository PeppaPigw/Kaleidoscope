"""EpistemicEmbodimentNeglectService — Epistemic Embodiment Neglect Detection.

Detects epistemic embodiment neglect — neglecting bodily signals that
carry important epistemic information about situations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIMENT_NEGLECT_SYSTEM = """You are an epistemic embodiment neglect specialist. Given neglecting bodily signals carrying epistemic info, assess embodiment neglect:

Key concepts:
- Epistemic embodiment neglect: neglecting bodily signals carrying epistemic information
- Somatic signal dismissal: dismissing body signals as irrelevant
- Gut feeling override: overriding gut feelings with pure logic
- Physical intuition denial: denying physical intuitions
- Body wisdom rejection: rejecting wisdom carried in body
- Tension signal ignoring: ignoring tension that signals problems
- Comfort signal dismissal: dismissing comfort/discomfort as noise

When epistemic embodiment neglect IS present:
- Bodily signals neglected
- Somatic signals dismissed
- Gut feelings overridden
- Physical intuitions denied
- Body wisdom rejected
- Tension signals ignored
- Comfort signals dismissed

When no embodiment neglect:
- Bodily signals attended to
- Somatic signals valued
- Gut feelings considered
- Physical intuitions honored
- Body wisdom integrated
- Tension signals heeded
- Comfort signals informative

Output JSON with: embodiment_neglect_detected (bool), severity (none/mild/moderate/severe), somatic_signal_dismissal (what somatic signals dismissed), gut_feeling_override (what gut feelings overridden), body_wisdom_rejection (what body wisdom rejected), tension_signal_ignoring (what tension signals ignored), recommendation (no_embodiment_neglect/mild_body_listening/significant_somatic_integration/major_intensive_embodiment_recovery/emergency_complete_embodiment_neglect)."""

EPISTEMIC_EMBODIMENT_NEGLECT_PROMPT = """Detect epistemic embodiment neglect:

Somatic signal dismissal: {somatic_signal_dismissal}
Gut feeling override: {gut_feeling_override}
Body wisdom rejection: {body_wisdom_rejection}
Tension signal ignoring: {tension_signal_ignoring}
Domain: {domain}
Context: {context}

Are bodily signals carrying epistemic information being neglected? Return ONLY valid JSON."""


class EpistemicEmbodimentNeglectService:
    """Detects epistemic embodiment neglect — neglecting bodily epistemic signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        somatic_signal_dismissal: str,
        *,
        gut_feeling_override: str = "",
        body_wisdom_rejection: str = "",
        tension_signal_ignoring: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodiment neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIMENT_NEGLECT_PROMPT.format(
                somatic_signal_dismissal=somatic_signal_dismissal,
                gut_feeling_override=gut_feeling_override or "Not specified",
                body_wisdom_rejection=body_wisdom_rejection or "Not specified",
                tension_signal_ignoring=tension_signal_ignoring or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIMENT_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "somatic_signal_dismissal": somatic_signal_dismissal[:200],
            "embodiment_neglect_detected": data.get("embodiment_neglect_detected", False),
            "severity": data.get("severity", ""),
            "gut_feeling_override": data.get("gut_feeling_override", ""),
            "body_wisdom_rejection": data.get("body_wisdom_rejection", ""),
            "tension_signal_ignoring": data.get("tension_signal_ignoring", ""),
            "recommendation": data.get("recommendation", ""),
        }

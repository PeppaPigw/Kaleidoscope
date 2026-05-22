"""EpistemicAuthenticityFatigueService — Epistemic Authenticity Fatigue Detection.

Detects epistemic authenticity fatigue — exhaustion from maintaining
intellectual authenticity under pressure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHENTICITY_FATIGUE_SYSTEM = """You are an epistemic authenticity fatigue specialist. Given exhaustion from maintaining authenticity, assess authenticity fatigue:

Key concepts:
- Epistemic authenticity fatigue: exhaustion from maintaining authenticity
- Integrity exhaustion: tired of being honest when it costs
- Authenticity burnout: worn out from constant genuine engagement
- Sincerity depletion: running out of energy for honest expression
- Courage fatigue: exhausted from standing by unpopular positions
- Vulnerability exhaustion: tired of being intellectually open
- Consistency strain: exhausted from maintaining coherent positions

When epistemic authenticity fatigue IS present:
- Exhaustion from maintaining authenticity
- Tired of honesty when it costs
- Worn out from genuine engagement
- Running out of energy for honesty
- Exhausted from unpopular positions
- Tired of being open
- Exhausted from consistency

When no authenticity fatigue:
- Energized by authenticity
- Honesty feels natural
- Genuine engagement sustainable
- Energy for honest expression
- Comfortable with positions
- Openness feels easy
- Consistency effortless

Output JSON with: authenticity_fatigue_detected (bool), severity (none/mild/moderate/severe), integrity_exhaustion (what tired of being honest about), authenticity_burnout (what worn out from), sincerity_depletion (what running out of energy for), courage_fatigue (what exhausted from standing by), recommendation (no_authenticity_fatigue/mild_rest_and_recovery/significant_sustainability_building/major_intensive_resilience_work/emergency_complete_authenticity_collapse)."""

EPISTEMIC_AUTHENTICITY_FATIGUE_PROMPT = """Detect epistemic authenticity fatigue:

Integrity exhaustion: {integrity_exhaustion}
Authenticity burnout: {authenticity_burnout}
Sincerity depletion: {sincerity_depletion}
Courage fatigue: {courage_fatigue}
Domain: {domain}
Context: {context}

Is there exhaustion from maintaining intellectual authenticity under pressure? Return ONLY valid JSON."""


class EpistemicAuthenticityFatigueService:
    """Detects epistemic authenticity fatigue — exhaustion from maintaining authenticity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        integrity_exhaustion: str,
        *,
        authenticity_burnout: str = "",
        sincerity_depletion: str = "",
        courage_fatigue: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authenticity fatigue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHENTICITY_FATIGUE_PROMPT.format(
                integrity_exhaustion=integrity_exhaustion,
                authenticity_burnout=authenticity_burnout or "Not specified",
                sincerity_depletion=sincerity_depletion or "Not specified",
                courage_fatigue=courage_fatigue or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHENTICITY_FATIGUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "integrity_exhaustion": integrity_exhaustion[:200],
            "authenticity_fatigue_detected": data.get("authenticity_fatigue_detected", False),
            "severity": data.get("severity", ""),
            "authenticity_burnout": data.get("authenticity_burnout", ""),
            "sincerity_depletion": data.get("sincerity_depletion", ""),
            "courage_fatigue": data.get("courage_fatigue", ""),
            "recommendation": data.get("recommendation", ""),
        }

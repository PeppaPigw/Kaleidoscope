"""EpistemicTemporalNostalgiaDistortionService — Epistemic Temporal Nostalgia Distortion Detection.

Detects epistemic temporal nostalgia distortion — idealizing the past while
denigrating the present, creating false comparisons across time periods.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_NOSTALGIA_DISTORTION_SYSTEM = """You are an epistemic temporal nostalgia distortion specialist. Given nostalgia distortion, assess temporal idealization:

Key concepts:
- Epistemic nostalgia distortion: idealizing past while denigrating present
- Rosy retrospection: remembering past as better than it was
- Decline narrative: framing present as degradation from golden age
- Survivorship bias temporal: only remembering best of past
- Selective memory: forgetting past problems while amplifying present ones
- Golden age fallacy: believing a specific past era was ideal
- Progress denial: refusing to acknowledge genuine improvements

When epistemic nostalgia distortion IS present:
- Past idealized
- Present denigrated
- Decline narrative imposed
- Only best of past remembered
- Past problems forgotten
- Golden age claimed
- Progress denied

When no nostalgia distortion:
- Past assessed accurately
- Present evaluated fairly
- Change assessed neutrally
- Full past remembered
- Past problems acknowledged
- No golden age claimed
- Progress and regress both noted

Output JSON with: nostalgia_distortion_detected (bool), severity (none/mild/moderate/severe), rosy_retrospection (what past idealized), decline_narrative (what decline claimed), survivorship_temporal (what selectively remembered), golden_age_fallacy (what golden age claimed), recommendation (no_nostalgia_distortion/mild_temporal_accuracy/significant_historical_realism/major_intensive_period_comparison/emergency_complete_nostalgia_distortion)."""

EPISTEMIC_TEMPORAL_NOSTALGIA_DISTORTION_PROMPT = """Detect epistemic temporal nostalgia distortion:

Rosy retrospection: {rosy_retrospection}
Decline narrative: {decline_narrative}
Survivorship temporal: {survivorship_temporal}
Golden age fallacy: {golden_age_fallacy}
Domain: {domain}
Context: {context}

Is the past being idealized while the present is denigrated? Return ONLY valid JSON."""


class EpistemicTemporalNostalgiaDistortionService:
    """Detects epistemic temporal nostalgia distortion — past idealization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rosy_retrospection: str,
        *,
        decline_narrative: str = "",
        survivorship_temporal: str = "",
        golden_age_fallacy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal nostalgia distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_NOSTALGIA_DISTORTION_PROMPT.format(
                rosy_retrospection=rosy_retrospection,
                decline_narrative=decline_narrative or "Not specified",
                survivorship_temporal=survivorship_temporal or "Not specified",
                golden_age_fallacy=golden_age_fallacy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_NOSTALGIA_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rosy_retrospection": rosy_retrospection[:200],
            "nostalgia_distortion_detected": data.get("nostalgia_distortion_detected", False),
            "severity": data.get("severity", ""),
            "decline_narrative": data.get("decline_narrative", ""),
            "survivorship_temporal": data.get("survivorship_temporal", ""),
            "golden_age_fallacy": data.get("golden_age_fallacy", ""),
            "recommendation": data.get("recommendation", ""),
        }

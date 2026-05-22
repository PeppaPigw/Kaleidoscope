"""EpistemicPhotoperiodismService — Epistemic Photoperiodism Detection.

Detects epistemic photoperiodism — intellectual activity patterns
triggered by the length of exposure to illuminating ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHOTOPERIODISM_SYSTEM = """You are an epistemic photoperiodism specialist. Given an intellectual activity pattern, assess whether exposure duration triggers specific responses:

Key concepts:
- Epistemic photoperiodism: activity triggered by exposure duration
- Day length: how long ideas are exposed to illumination
- Short-day response: activity triggered by brief exposure
- Long-day response: activity triggered by extended exposure
- Critical period: minimum exposure needed to trigger response
- Flowering: intellectual productivity triggered by right exposure
- Dormancy: intellectual dormancy triggered by short exposure

When epistemic photoperiodism IS present:
- Intellectual activity patterns triggered by exposure duration
- Duration of exposure to illuminating ideas matters
- Brief exposure triggering specific intellectual responses
- Extended exposure triggering different responses
- Minimum exposure needed before response triggers
- Intellectual productivity triggered by right exposure duration
- Intellectual dormancy triggered by insufficient exposure

When constant activity is present:
- Intellectual activity independent of exposure duration
- Duration of exposure irrelevant
- Same response regardless of exposure length
- No different responses to different durations
- No minimum exposure threshold
- Productivity independent of exposure
- No dormancy from insufficient exposure

Output JSON with: photoperiodism_present (bool), severity (none/mild/moderate/severe), exposure (what illuminating ideas), duration (what exposure duration matters), response (what activity is triggered), critical_period (what minimum exposure needed), recommendation (constant_activity/mild_sensitivity/significant_photoperiodism/major_duration_dependence/optimize_exposure_duration)."""

EPISTEMIC_PHOTOPERIODISM_PROMPT = """Detect epistemic photoperiodism:

Exposure: {exposure}
Duration: {duration}
Response: {response}
Critical period: {critical_period}
Domain: {domain}
Context: {context}

Are intellectual activity patterns triggered by the duration of exposure to illuminating ideas? Return ONLY valid JSON."""


class EpistemicPhotoperiodismService:
    """Detects epistemic photoperiodism — activity triggered by exposure duration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exposure: str,
        *,
        duration: str = "",
        response: str = "",
        critical_period: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic photoperiodism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHOTOPERIODISM_PROMPT.format(
                exposure=exposure,
                duration=duration or "Not specified",
                response=response or "Not specified",
                critical_period=critical_period or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHOTOPERIODISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exposure": exposure[:200],
            "photoperiodism_present": data.get("photoperiodism_present", False),
            "severity": data.get("severity", ""),
            "duration": data.get("duration", ""),
            "response": data.get("response", ""),
            "critical_period": data.get("critical_period", ""),
            "recommendation": data.get("recommendation", ""),
        }

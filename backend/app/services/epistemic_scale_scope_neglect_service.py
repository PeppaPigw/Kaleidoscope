"""EpistemicScaleScopeNeglectService - Epistemic Scale Scope Neglect Detection.

Detects scope neglect failing to scale responses to magnitude of phenomena.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_SCOPE_NEGLECT_SYSTEM = """You are an epistemic scale scope neglect specialist. Given magnitude insensitivity, assess scope neglect:

Key concepts:
- Epistemic scale scope neglect: failing to scale responses to magnitude of phenomena
- Magnitude insensitivity: response does not change with size
- Unit bias: treating one unit as the natural amount regardless of scale
- Proportion blindness: ignoring ratios and relative magnitude
- Scale invariance assumption: assuming reasoning transfers unchanged across scale

When scope neglect IS present:
- Response is insensitive to magnitude
- Unit bias shapes judgment
- Proportions are ignored
- Scale changes are treated as irrelevant
- Large differences receive similar treatment

When no scope neglect:
- Responses scale with magnitude
- Units are chosen appropriately
- Proportions are considered
- Scale effects are examined
- Large differences change conclusions

Output JSON with: scope_neglect_detected (bool), severity (none/mild/moderate/severe), unit_bias (what unit bias appears), proportion_blindness (what proportions are ignored), scale_invariance_assumption (what scale invariance is assumed), recommendation (no_scope_neglect/mild_magnitude_check/significant_scale_recalibration/major_scope_analysis/emergency_complete_scope_neglect)."""

EPISTEMIC_SCALE_SCOPE_NEGLECT_PROMPT = """Detect epistemic scale scope neglect:

Magnitude insensitivity: {magnitude_insensitivity}
Unit bias: {unit_bias}
Proportion blindness: {proportion_blindness}
Scale invariance assumption: {scale_invariance_assumption}
Domain: {domain}
Context: {context}

Is the response failing to scale with the magnitude of the phenomenon? Return ONLY valid JSON."""


class EpistemicScaleScopeNeglectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        magnitude_insensitivity: str,
        *,
        unit_bias: str = "",
        proportion_blindness: str = "",
        scale_invariance_assumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_SCOPE_NEGLECT_PROMPT.format(
                magnitude_insensitivity=magnitude_insensitivity,
                unit_bias=unit_bias or "Not specified",
                proportion_blindness=proportion_blindness or "Not specified",
                scale_invariance_assumption=scale_invariance_assumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_SCOPE_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "magnitude_insensitivity": magnitude_insensitivity[:200],
            "scope_neglect_detected": data.get("scope_neglect_detected", False),
            "severity": data.get("severity", ""),
            "unit_bias": data.get("unit_bias", ""),
            "proportion_blindness": data.get("proportion_blindness", ""),
            "scale_invariance_assumption": data.get("scale_invariance_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }

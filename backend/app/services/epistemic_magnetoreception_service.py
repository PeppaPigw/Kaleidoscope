"""EpistemicMagnetoreceptionService — Epistemic Magnetoreception Detection.

Detects epistemic magnetoreception — sensing invisible intellectual
fields that provide orientation without conscious awareness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MAGNETORECEPTION_SYSTEM = """You are an epistemic magnetoreception specialist. Given an orientation pattern, assess whether invisible fields provide unconscious guidance:

Key concepts:
- Epistemic magnetoreception: sensing invisible intellectual fields
- Invisible field: intellectual force not consciously perceived
- Orientation: knowing direction without knowing how
- Unconscious guidance: being guided without awareness
- Inclination: sensing the angle of the intellectual field
- Declination: difference between true and perceived north
- Magnetic storm: disruption of the guiding field

When epistemic magnetoreception IS present:
- Sensing invisible intellectual fields for orientation
- Invisible forces providing direction
- Knowing intellectual direction without knowing how
- Being guided by forces outside conscious awareness
- Sensing the angle and strength of intellectual fields
- Difference between true direction and perceived direction
- Disruptions to the guiding field causing disorientation

When conscious navigation is present:
- Using visible landmarks for orientation
- Forces clearly visible and understood
- Knowing direction through conscious reasoning
- Guidance through deliberate awareness
- Consciously measuring direction
- True and perceived direction aligned
- No disruption to navigation

Output JSON with: magnetoreception_present (bool), severity (none/mild/moderate/severe), field (what invisible field provides guidance), orientation (what direction it provides), unconscious (what guidance happens without awareness), storm (what disruptions occur), recommendation (conscious_navigation/mild_field_sensing/significant_magnetoreception/major_unconscious_guidance/make_field_influence_conscious)."""

EPISTEMIC_MAGNETORECEPTION_PROMPT = """Detect epistemic magnetoreception:

Field: {field}
Orientation: {orientation}
Unconscious: {unconscious}
Storm: {storm}
Domain: {domain}
Context: {context}

Are invisible intellectual fields providing orientation without conscious awareness? Return ONLY valid JSON."""


class EpistemicMagnetoreceptionService:
    """Detects epistemic magnetoreception — unconscious guidance by invisible fields."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        field: str,
        *,
        orientation: str = "",
        unconscious: str = "",
        storm: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic magnetoreception."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MAGNETORECEPTION_PROMPT.format(
                field=field,
                orientation=orientation or "Not specified",
                unconscious=unconscious or "Not specified",
                storm=storm or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MAGNETORECEPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "field": field[:200],
            "magnetoreception_present": data.get("magnetoreception_present", False),
            "severity": data.get("severity", ""),
            "orientation": data.get("orientation", ""),
            "unconscious": data.get("unconscious", ""),
            "storm": data.get("storm", ""),
            "recommendation": data.get("recommendation", ""),
        }

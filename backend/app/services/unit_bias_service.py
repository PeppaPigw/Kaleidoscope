"""UnitBiasService — Unit Bias Detection.

Detects unit bias — the tendency to want to complete a "unit"
regardless of whether the unit size is appropriate. Geier,
Rozin & Doros (2006). People eat more when given larger plates,
finish the whole bag regardless of size, and treat arbitrary
units as the "right" amount. One serving = one unit = enough,
regardless of actual quantity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNIT_BIAS_SYSTEM = """You are a unit bias specialist. Given a consumption or allocation decision, assess whether arbitrary unit boundaries are determining quantity rather than actual need:

Key concepts (Geier, Rozin & Doros, 2006):
- Unit bias: treating one unit as the appropriate amount regardless of unit size
- Completion drive: desire to finish what was started (clean plate, whole episode)
- Arbitrary units: the "unit" is often determined by packaging, not need
- Portion size effect: larger portions lead to more consumption
- Default effect overlap: the unit becomes the default amount
- Anchoring overlap: the unit size anchors expectations

When unit bias IS present:
- Consuming more because the container/portion is larger
- "Finishing the bag" regardless of hunger
- Treating one meeting/sprint/quarter as the natural unit for a task
- Allocating resources based on arbitrary unit boundaries
- "One more episode" when the episode length is arbitrary
- Package size determining consumption rather than need

When unit-based behavior IS appropriate:
- The unit genuinely represents the optimal amount
- Completion has genuine value (half-measures would be wasteful)
- The unit was deliberately sized based on research/need
- Breaking the unit would create genuine problems (half a pill, partial deployment)
- The person consciously chose the unit size

Output JSON with: unit_bias_present (bool), severity (none/mild/moderate/severe), unit (what is being treated as one unit), unit_size (how large is the unit), appropriate_amount (what amount would actually be optimal), size_determinant (what determined the unit size — need or arbitrary?), completion_drive (bool — is desire to finish driving behavior?), packaging_effect (bool — is packaging determining consumption?), default_anchoring (bool — is the unit acting as an anchor?), overconsumption (how much excess results from unit bias?), awareness (does the person recognize the unit is arbitrary?), alternative_framing (how could the unit be reframed?), recommendation (unit_appropriate/mild_unit_bias/significant_overconsumption/major_unit_bias/size_to_need)."""

UNIT_BIAS_PROMPT = """Detect unit bias:

Situation: {situation}
Unit being used: {unit}
Actual need: {need}
Unit origin: {origin}
Domain: {domain}
Context: {context}

Is an arbitrary unit boundary determining quantity rather than actual need? Return ONLY valid JSON."""


class UnitBiasService:
    """Detects unit bias — arbitrary units determining quantity over actual need."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        unit: str = "",
        need: str = "",
        origin: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect unit bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNIT_BIAS_PROMPT.format(
                situation=situation,
                unit=unit or "Not specified",
                need=need or "Not specified",
                origin=origin or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNIT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "unit_bias_present": data.get("unit_bias_present", False),
            "severity": data.get("severity", ""),
            "unit": data.get("unit", ""),
            "unit_size": data.get("unit_size", ""),
            "appropriate_amount": data.get("appropriate_amount", ""),
            "size_determinant": data.get("size_determinant", ""),
            "completion_drive": data.get("completion_drive", False),
            "packaging_effect": data.get("packaging_effect", False),
            "default_anchoring": data.get("default_anchoring", False),
            "overconsumption": data.get("overconsumption", ""),
            "awareness": data.get("awareness", ""),
            "alternative_framing": data.get("alternative_framing", ""),
            "recommendation": data.get("recommendation", ""),
        }

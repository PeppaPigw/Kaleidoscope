"""EpistemicNeutrinoOscillationService — Epistemic Neutrino Oscillation Detection.

Detects epistemic neutrino oscillation — ideas changing their fundamental
type as they propagate through intellectual space.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NEUTRINO_OSCILLATION_SYSTEM = """You are an epistemic neutrino oscillation specialist. Given an intellectual propagation, assess whether ideas change type as they travel:

Key concepts:
- Epistemic neutrino oscillation: ideas changing type during propagation
- Flavor mixing: different types blending during travel
- Mass eigenstate: true propagation state differing from observed type
- Mixing angle: degree of type-changing
- Oscillation length: distance for complete type change
- MSW effect: medium enhancing the oscillation
- Sterile type: type that doesn't interact at all

When epistemic neutrino oscillation IS present:
- Ideas changing their fundamental type during propagation
- Different types blending as ideas travel
- True nature differing from observed type
- Measurable degree of type-changing
- Characteristic distance for complete transformation
- Medium enhancing the type change
- Some types not interacting at all

When stable type is present:
- Ideas maintaining their type during propagation
- No blending between types
- True nature matching observed type
- No type-changing
- No transformation distance
- Medium not affecting type
- All types interacting normally

Output JSON with: neutrino_oscillation_present (bool), severity (none/mild/moderate/severe), flavor_mixing (what type blending), mass_eigenstate (what true nature), mixing_angle (what degree of change), msw_effect (what medium enhancement), recommendation (stable_type/mild_oscillation/significant_neutrino_oscillation/major_type_change/track_oscillation_pattern)."""

EPISTEMIC_NEUTRINO_OSCILLATION_PROMPT = """Detect epistemic neutrino oscillation:

Flavor mixing: {flavor_mixing}
Mass eigenstate: {mass_eigenstate}
Mixing angle: {mixing_angle}
MSW effect: {msw_effect}
Domain: {domain}
Context: {context}

Are ideas changing their fundamental type as they propagate through intellectual space? Return ONLY valid JSON."""


class EpistemicNeutrinoOscillationService:
    """Detects epistemic neutrino oscillation — ideas changing type during propagation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flavor_mixing: str,
        *,
        mass_eigenstate: str = "",
        mixing_angle: str = "",
        msw_effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic neutrino oscillation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NEUTRINO_OSCILLATION_PROMPT.format(
                flavor_mixing=flavor_mixing,
                mass_eigenstate=mass_eigenstate or "Not specified",
                mixing_angle=mixing_angle or "Not specified",
                msw_effect=msw_effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NEUTRINO_OSCILLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flavor_mixing": flavor_mixing[:200],
            "neutrino_oscillation_present": data.get("neutrino_oscillation_present", False),
            "severity": data.get("severity", ""),
            "mass_eigenstate": data.get("mass_eigenstate", ""),
            "mixing_angle": data.get("mixing_angle", ""),
            "msw_effect": data.get("msw_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }

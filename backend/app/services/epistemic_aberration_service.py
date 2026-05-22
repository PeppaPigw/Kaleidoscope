"""EpistemicAberrationService — Epistemic Aberration Detection.

Detects epistemic aberration — intellectual lenses that distort ideas
differently at their edges than at their center.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABERRATION_SYSTEM = """You are an epistemic aberration specialist. Given a lens distortion pattern, assess whether intellectual lenses distort ideas differently at edges vs center:

Key concepts:
- Epistemic aberration: lenses distorting ideas differently at edges
- Chromatic: different idea types focused at different points
- Spherical: ideas at edges focused differently than center
- Coma: off-axis ideas appearing comet-shaped
- Astigmatism: ideas focused differently in different planes
- Field curvature: flat ideas appearing curved through lens
- Distortion: straight ideas appearing bent

When epistemic aberration IS present:
- Intellectual lenses distorting ideas differently at edges
- Different idea types focused at different points
- Ideas at periphery distorted more than central ones
- Off-axis ideas appearing distorted
- Ideas focused differently depending on perspective
- Flat/simple ideas appearing curved through the lens
- Straight/clear ideas appearing bent

When perfect optics is present:
- All ideas focused equally regardless of position
- All idea types focused at same point
- Edge and center ideas equally clear
- Off-axis ideas undistorted
- Same focus regardless of perspective
- Simple ideas remaining simple through lens
- Clear ideas remaining straight

Output JSON with: aberration_present (bool), severity (none/mild/moderate/severe), chromatic (what types focused differently), spherical (what edge distortion), coma (what off-axis distortion), astigmatism (what perspective-dependent focus), recommendation (perfect_optics/mild_aberration/significant_aberration/major_lens_distortion/correct_lens_design)."""

EPISTEMIC_ABERRATION_PROMPT = """Detect epistemic aberration:

Chromatic: {chromatic}
Spherical: {spherical}
Coma: {coma}
Astigmatism: {astigmatism}
Domain: {domain}
Context: {context}

Are intellectual lenses distorting ideas differently at their edges than at their center? Return ONLY valid JSON."""


class EpistemicAberrationService:
    """Detects epistemic aberration — lens distortion at edges."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        chromatic: str,
        *,
        spherical: str = "",
        coma: str = "",
        astigmatism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic aberration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABERRATION_PROMPT.format(
                chromatic=chromatic,
                spherical=spherical or "Not specified",
                coma=coma or "Not specified",
                astigmatism=astigmatism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABERRATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "chromatic": chromatic[:200],
            "aberration_present": data.get("aberration_present", False),
            "severity": data.get("severity", ""),
            "spherical": data.get("spherical", ""),
            "coma": data.get("coma", ""),
            "astigmatism": data.get("astigmatism", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicHologramService — Epistemic Hologram Detection.

Detects epistemic hologram — ideas that appear three-dimensional but
are actually encoded on a two-dimensional surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOLOGRAM_SYSTEM = """You are an epistemic hologram specialist. Given an idea dimensionality pattern, assess whether ideas appear 3D but are encoded on a 2D surface:

Key concepts:
- Epistemic hologram: 3D appearance from 2D encoding
- Reference beam: the framework that enables reconstruction
- Interference pattern: encoded information on the surface
- Reconstruction: recreating the 3D appearance from 2D
- Viewing angle: different perspectives showing different aspects
- Depth illusion: appearance of depth that isn't real
- Holographic principle: all information on the boundary

When epistemic hologram IS present:
- Ideas appearing three-dimensional but encoded on flat surface
- Framework enabling the reconstruction of depth
- Encoded information creating the appearance
- Recreating depth from flat encoding
- Different perspectives showing different aspects
- Appearance of depth that isn't actually there
- All information actually residing on the boundary

When true depth is present:
- Ideas genuinely three-dimensional
- No framework needed for depth
- Information distributed through volume
- Depth directly observable
- Same depth from all perspectives
- Real depth, not illusion
- Information throughout, not just boundary

Output JSON with: hologram_present (bool), severity (none/mild/moderate/severe), reference_beam (what framework enables reconstruction), interference (what encoding creates appearance), depth_illusion (what false depth appears), viewing_angle (what perspective dependence), recommendation (true_depth/mild_encoding/significant_hologram/major_dimensional_illusion/acknowledge_flat_encoding)."""

EPISTEMIC_HOLOGRAM_PROMPT = """Detect epistemic hologram:

Reference beam: {reference_beam}
Interference: {interference}
Depth illusion: {depth_illusion}
Viewing angle: {viewing_angle}
Domain: {domain}
Context: {context}

Do ideas appear three-dimensional but are actually encoded on a two-dimensional surface? Return ONLY valid JSON."""


class EpistemicHologramService:
    """Detects epistemic hologram — 3D appearance from 2D encoding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reference_beam: str,
        *,
        interference: str = "",
        depth_illusion: str = "",
        viewing_angle: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hologram."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOLOGRAM_PROMPT.format(
                reference_beam=reference_beam,
                interference=interference or "Not specified",
                depth_illusion=depth_illusion or "Not specified",
                viewing_angle=viewing_angle or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOLOGRAM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reference_beam": reference_beam[:200],
            "hologram_present": data.get("hologram_present", False),
            "severity": data.get("severity", ""),
            "interference": data.get("interference", ""),
            "depth_illusion": data.get("depth_illusion", ""),
            "viewing_angle": data.get("viewing_angle", ""),
            "recommendation": data.get("recommendation", ""),
        }

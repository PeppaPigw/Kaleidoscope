"""EpistemicAstigmatismService — Epistemic Astigmatism Detection.

Detects epistemic astigmatism — distorted intellectual perception from
irregular curvature causing ideas to appear warped or stretched.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ASTIGMATISM_SYSTEM = """You are an epistemic astigmatism specialist. Given intellectual perception, assess whether irregular curvature distorts ideas:

Key concepts:
- Epistemic astigmatism: distorted perception from irregular curvature
- Meridional difference: different focus in different directions
- Cylindrical error: correction needed for directional distortion
- Regular astigmatism: predictable distortion pattern
- Irregular astigmatism: unpredictable distortion
- Corneal topography: mapping the distortion surface
- Toric correction: lens shaped to compensate for asymmetry

When epistemic astigmatism IS present:
- Distorted perception from irregular intellectual curvature
- Different focus quality in different directions
- Directional distortion needing correction
- Predictable or unpredictable distortion patterns
- Mappable distortion surface
- Need for asymmetric correction
- Ideas appearing warped or stretched

When healthy perception is present:
- Undistorted perception
- Uniform focus in all directions
- No directional distortion
- No distortion patterns
- Smooth perception surface
- No correction needed
- Ideas appearing as they are

Output JSON with: astigmatism_present (bool), severity (none/mild/moderate/severe), meridional_difference (what directional variation), cylindrical_error (what directional distortion), irregular_pattern (what unpredictable warping), corneal_topography (what distortion mapping), recommendation (healthy_perception/mild_astigmatism/significant_astigmatism/major_distortion/correct_intellectual_curvature)."""

EPISTEMIC_ASTIGMATISM_PROMPT = """Detect epistemic astigmatism:

Meridional difference: {meridional_difference}
Cylindrical error: {cylindrical_error}
Irregular pattern: {irregular_pattern}
Corneal topography: {corneal_topography}
Domain: {domain}
Context: {context}

Is irregular intellectual curvature distorting perception, making ideas appear warped? Return ONLY valid JSON."""


class EpistemicAstigmatismService:
    """Detects epistemic astigmatism — distorted perception from irregular curvature."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meridional_difference: str,
        *,
        cylindrical_error: str = "",
        irregular_pattern: str = "",
        corneal_topography: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic astigmatism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ASTIGMATISM_PROMPT.format(
                meridional_difference=meridional_difference,
                cylindrical_error=cylindrical_error or "Not specified",
                irregular_pattern=irregular_pattern or "Not specified",
                corneal_topography=corneal_topography or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ASTIGMATISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meridional_difference": meridional_difference[:200],
            "astigmatism_present": data.get("astigmatism_present", False),
            "severity": data.get("severity", ""),
            "cylindrical_error": data.get("cylindrical_error", ""),
            "irregular_pattern": data.get("irregular_pattern", ""),
            "corneal_topography": data.get("corneal_topography", ""),
            "recommendation": data.get("recommendation", ""),
        }

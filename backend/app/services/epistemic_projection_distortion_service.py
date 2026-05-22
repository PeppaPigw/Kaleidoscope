"""EpistemicProjectionDistortionService — Epistemic Projection Distortion Detection.

Detects epistemic projection distortion — map projections distorting
the knowledge territory, making some areas appear larger or smaller.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROJECTION_DISTORTION_SYSTEM = """You are an epistemic projection distortion specialist. Given a knowledge representation, assess whether the projection distorts territory:

Key concepts:
- Epistemic projection distortion: representation distorting knowledge territory
- Area distortion: some areas appearing larger or smaller than reality
- Shape distortion: shapes of knowledge areas distorted
- Center bias: areas near the center appearing more important
- Periphery shrinkage: peripheral areas appearing smaller
- Projection choice: choice of projection introducing systematic bias
- Unavoidable tradeoff: all projections distort something

When projection distortion IS present:
- Knowledge representation distorting actual territory
- Some areas appearing larger or smaller than they are
- Shapes of knowledge areas distorted by representation
- Central areas appearing disproportionately important
- Peripheral areas appearing smaller than they are
- Choice of framework introducing systematic bias
- Distortion not acknowledged or corrected for

When accurate representation is present:
- Knowledge representation matching territory
- Areas appearing at appropriate relative size
- Shapes of knowledge areas preserved
- No center bias in representation
- Peripheral areas appropriately represented
- Framework chosen to minimize relevant distortion
- Any distortion acknowledged and corrected for

Output JSON with: projection_distortion (bool), severity (none/mild/moderate/severe), representation (what representation distorts), area_distortion (what areas are distorted), bias (what systematic bias), correction_needed (what correction is needed), recommendation (accurate_representation/mild_distortion/significant_projection_bias/major_territory_distortion/acknowledge_and_correct)."""

EPISTEMIC_PROJECTION_DISTORTION_PROMPT = """Detect epistemic projection distortion:

Representation: {representation}
Area distortion: {area_distortion}
Bias: {bias}
Correction needed: {correction_needed}
Domain: {domain}
Context: {context}

Is the knowledge representation distorting the actual territory? Return ONLY valid JSON."""


class EpistemicProjectionDistortionService:
    """Detects epistemic projection distortion — representation distorting territory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        representation: str,
        *,
        area_distortion: str = "",
        bias: str = "",
        correction_needed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic projection distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROJECTION_DISTORTION_PROMPT.format(
                representation=representation,
                area_distortion=area_distortion or "Not specified",
                bias=bias or "Not specified",
                correction_needed=correction_needed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROJECTION_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "representation": representation[:200],
            "projection_distortion": data.get("projection_distortion", False),
            "severity": data.get("severity", ""),
            "area_distortion": data.get("area_distortion", ""),
            "bias": data.get("bias", ""),
            "correction_needed": data.get("correction_needed", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicRefractionService — Epistemic Refraction Detection.

Detects epistemic refraction — knowledge bending as it passes
between different contexts, distorting its meaning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REFRACTION_SYSTEM = """You are an epistemic refraction specialist. Given a knowledge transfer pattern, assess whether knowledge bends between contexts:

Key concepts:
- Epistemic refraction: knowledge bending as it crosses context boundaries
- Context boundary: where one domain meets another
- Meaning distortion: meaning changing as knowledge crosses boundaries
- Medium change: different contexts acting as different media
- Angle of incidence: how knowledge enters new context
- Apparent position: knowledge appearing in wrong position after refraction
- Total internal reflection: knowledge unable to cross boundary at all

When epistemic refraction IS present:
- Knowledge bending as it passes between contexts
- Meaning distorting at context boundaries
- Different contexts changing knowledge direction
- Knowledge appearing in wrong position after transfer
- Angle of entry affecting degree of distortion
- Some knowledge unable to cross boundaries at all
- Systematic bending in predictable directions

When undistorted transfer is present:
- Knowledge maintaining meaning across contexts
- No distortion at context boundaries
- Contexts not changing knowledge direction
- Knowledge appearing in correct position after transfer
- Transfer angle not affecting meaning
- Knowledge crossing boundaries freely
- No systematic bending

Output JSON with: refraction_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge refracts), boundary (what boundary causes refraction), distortion (what distortion occurs), direction (what direction it bends), recommendation (undistorted_transfer/mild_bending/significant_refraction/major_distortion/correct_for_context_change)."""

EPISTEMIC_REFRACTION_PROMPT = """Detect epistemic refraction:

Knowledge: {knowledge}
Boundary: {boundary}
Distortion: {distortion}
Direction: {direction}
Domain: {domain}
Context: {context}

Is knowledge bending and distorting as it passes between contexts? Return ONLY valid JSON."""


class EpistemicRefractionService:
    """Detects epistemic refraction — knowledge bending between contexts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        boundary: str = "",
        distortion: str = "",
        direction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic refraction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REFRACTION_PROMPT.format(
                knowledge=knowledge,
                boundary=boundary or "Not specified",
                distortion=distortion or "Not specified",
                direction=direction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REFRACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "refraction_present": data.get("refraction_present", False),
            "severity": data.get("severity", ""),
            "boundary": data.get("boundary", ""),
            "distortion": data.get("distortion", ""),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }

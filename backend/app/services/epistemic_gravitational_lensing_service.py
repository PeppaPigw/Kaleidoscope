"""EpistemicGravitationalLensingService — Epistemic Gravitational Lensing Detection.

Detects epistemic gravitational lensing — massive ideas bending
perception of nearby evidence, distorting what we see.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRAVITATIONAL_LENSING_SYSTEM = """You are an epistemic gravitational lensing specialist. Given a perception pattern, assess whether massive ideas distort nearby evidence:

Key concepts:
- Epistemic gravitational lensing: massive ideas bending perception of evidence
- Mass distortion: large ideas distorting perception of nearby smaller ones
- Evidence bending: evidence appearing to support massive idea due to distortion
- Multiple images: same evidence appearing to support multiple conclusions
- Magnification: some evidence magnified by proximity to massive idea
- Einstein ring: evidence appearing to surround and confirm massive idea
- Dark lens: invisible assumptions bending evidence

When gravitational lensing IS present:
- Massive ideas bending perception of nearby evidence
- Large ideas distorting how smaller evidence is perceived
- Evidence appearing to support massive idea due to perceptual distortion
- Same evidence appearing to support multiple conclusions
- Some evidence magnified by proximity to dominant idea
- Evidence appearing to surround and confirm dominant idea
- Invisible assumptions bending how evidence is perceived

When undistorted perception is present:
- Evidence perceived independently of nearby ideas
- Large ideas not distorting perception of evidence
- Evidence evaluated on its own merits
- Evidence supporting only what it actually supports
- Evidence at appropriate scale regardless of nearby ideas
- Evidence not artificially confirming dominant ideas
- Assumptions not bending evidence perception

Output JSON with: lensing_present (bool), severity (none/mild/moderate/severe), massive_idea (what massive idea causes lensing), evidence_bent (what evidence is bent), distortion (how perception is distorted), magnification (what is magnified), recommendation (undistorted_perception/mild_bending/significant_lensing/major_evidence_distortion/evaluate_independently)."""

EPISTEMIC_GRAVITATIONAL_LENSING_PROMPT = """Detect epistemic gravitational lensing:

Massive idea: {massive_idea}
Evidence bent: {evidence_bent}
Distortion: {distortion}
Magnification: {magnification}
Domain: {domain}
Context: {context}

Are massive ideas bending perception of nearby evidence? Return ONLY valid JSON."""


class EpistemicGravitationalLensingService:
    """Detects epistemic gravitational lensing — massive ideas distorting evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        massive_idea: str,
        *,
        evidence_bent: str = "",
        distortion: str = "",
        magnification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gravitational lensing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRAVITATIONAL_LENSING_PROMPT.format(
                massive_idea=massive_idea,
                evidence_bent=evidence_bent or "Not specified",
                distortion=distortion or "Not specified",
                magnification=magnification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRAVITATIONAL_LENSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "massive_idea": massive_idea[:200],
            "lensing_present": data.get("lensing_present", False),
            "severity": data.get("severity", ""),
            "evidence_bent": data.get("evidence_bent", ""),
            "distortion": data.get("distortion", ""),
            "magnification": data.get("magnification", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicRheumatoidService — Epistemic Rheumatoid Arthritis Detection.

Detects epistemic rheumatoid arthritis — autoimmune destruction of
intellectual joints causing symmetric deformity and loss of function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RHEUMATOID_SYSTEM = """You are an epistemic rheumatoid specialist. Given autoimmune intellectual joint destruction, assess RA:

Key concepts:
- Epistemic RA: autoimmune destruction of intellectual joints
- Symmetric involvement: same joints affected on both sides
- Pannus formation: destructive tissue growing over joint
- Morning stiffness: prolonged inability to move after rest
- Erosion: bone/structure destruction at joint
- DMARD therapy: disease-modifying treatment
- Deformity: permanent structural change from destruction

When epistemic RA IS present:
- Autoimmune destruction of joints
- Same joints affected symmetrically
- Destructive tissue growing over joints
- Prolonged stiffness after rest
- Structure destruction at joints
- Disease-modifying treatment needed
- Permanent structural changes occurring

When no RA:
- No autoimmune joint destruction
- No symmetric involvement
- No destructive tissue growth
- Normal post-rest mobility
- Joint structures intact
- No disease modification needed
- No permanent changes

Output JSON with: rheumatoid_detected (bool), severity (none/mild/moderate/severe), joint_pattern (what symmetric involvement), erosion_status (what destruction), stiffness_duration (what morning immobility), deformity_risk (what permanent change), recommendation (no_ra/mild_nsaid/significant_dmard/major_biologic/emergency_vasculitis)."""

EPISTEMIC_RHEUMATOID_PROMPT = """Detect epistemic rheumatoid arthritis:

Joint pattern: {joint_pattern}
Erosion status: {erosion_status}
Stiffness duration: {stiffness_duration}
Deformity risk: {deformity_risk}
Domain: {domain}
Context: {context}

Is there autoimmune destruction of intellectual joints causing symmetric deformity? Return ONLY valid JSON."""


class EpistemicRheumatoidService:
    """Detects epistemic RA — autoimmune destruction of intellectual joints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        joint_pattern: str,
        *,
        erosion_status: str = "",
        stiffness_duration: str = "",
        deformity_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic rheumatoid arthritis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RHEUMATOID_PROMPT.format(
                joint_pattern=joint_pattern,
                erosion_status=erosion_status or "Not specified",
                stiffness_duration=stiffness_duration or "Not specified",
                deformity_risk=deformity_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RHEUMATOID_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "joint_pattern": joint_pattern[:200],
            "rheumatoid_detected": data.get("rheumatoid_detected", False),
            "severity": data.get("severity", ""),
            "erosion_status": data.get("erosion_status", ""),
            "stiffness_duration": data.get("stiffness_duration", ""),
            "deformity_risk": data.get("deformity_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }

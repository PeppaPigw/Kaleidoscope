"""EpistemicProjectiveIdentificationService — Epistemic Projective Identification Detection.

Detects epistemic projective identification — projecting unwanted intellectual
aspects onto another and then pressuring them to actually become that projection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROJECTIVE_IDENTIFICATION_SYSTEM = """You are an epistemic projective identification specialist. Given projection with pressure to embody, assess projective identification:

Key concepts:
- Epistemic projective identification: projecting then pressuring embodiment
- Evacuation: getting rid of unwanted intellectual aspects
- Interpersonal pressure: making other actually become projection
- Containment demand: other must hold projected material
- Identity alteration: target begins to embody projection
- Unconscious communication: conveying experience through enactment
- Mutual entanglement: both parties caught in dynamic

When epistemic projective identification IS present:
- Projecting then pressuring
- Getting rid of unwanted aspects
- Making other become projection
- Other must hold material
- Target embodying projection
- Conveying through enactment
- Both caught in dynamic

When no projective identification:
- Owning own aspects
- Keeping unwanted internal
- Others remain themselves
- No containment demand
- Target identity intact
- Direct communication
- Independent functioning

Output JSON with: projective_identification_detected (bool), severity (none/mild/moderate/severe), evacuation_pattern (what getting rid), pressure_type (what making become), identity_alteration (what embodying), entanglement_level (what caught), recommendation (no_projective_identification/mild_boundary_work/significant_containment_therapy/major_intensive_disentanglement/emergency_identity_loss)."""

EPISTEMIC_PROJECTIVE_IDENTIFICATION_PROMPT = """Detect epistemic projective identification:

Evacuation pattern: {evacuation_pattern}
Pressure type: {pressure_type}
Identity alteration: {identity_alteration}
Entanglement level: {entanglement_level}
Domain: {domain}
Context: {context}

Is there projection of unwanted aspects with pressure on other to embody them? Return ONLY valid JSON."""


class EpistemicProjectiveIdentificationService:
    """Detects epistemic projective identification — projection with embodiment pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evacuation_pattern: str,
        *,
        pressure_type: str = "",
        identity_alteration: str = "",
        entanglement_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic projective identification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROJECTIVE_IDENTIFICATION_PROMPT.format(
                evacuation_pattern=evacuation_pattern,
                pressure_type=pressure_type or "Not specified",
                identity_alteration=identity_alteration or "Not specified",
                entanglement_level=entanglement_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROJECTIVE_IDENTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evacuation_pattern": evacuation_pattern[:200],
            "projective_identification_detected": data.get("projective_identification_detected", False),
            "severity": data.get("severity", ""),
            "pressure_type": data.get("pressure_type", ""),
            "identity_alteration": data.get("identity_alteration", ""),
            "entanglement_level": data.get("entanglement_level", ""),
            "recommendation": data.get("recommendation", ""),
        }

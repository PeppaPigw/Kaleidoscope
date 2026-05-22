"""EpistemicScaleBoundaryArbitrarienessService — Epistemic Scale Boundary Arbitrariness Detection.

Detects epistemic scale boundary arbitrariness — treating arbitrary scale boundaries
as natural joints, when different boundary choices would yield different conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_BOUNDARY_ARBITRARINESS_SYSTEM = """You are an epistemic scale boundary arbitrariness specialist. Given boundary choices, assess arbitrariness risks:

Key concepts:
- Epistemic boundary arbitrariness: treating chosen boundaries as natural
- Gerrymandering: drawing boundaries to produce desired conclusions
- Threshold effects: arbitrary thresholds creating false categories
- Temporal boundary: arbitrary start/end dates changing conclusions
- Spatial boundary: arbitrary geographic boundaries changing patterns
- Categorical boundary: arbitrary category definitions changing membership
- Resolution dependence: conclusions changing with measurement resolution

When epistemic boundary arbitrariness IS present:
- Boundaries treated as natural
- Gerrymandering suspected
- Arbitrary thresholds creating categories
- Temporal boundaries changing conclusions
- Spatial boundaries changing patterns
- Categories arbitrarily defined
- Resolution affecting conclusions

When no boundary arbitrariness:
- Boundaries acknowledged as chosen
- Boundary sensitivity tested
- Thresholds justified
- Temporal boundaries robust
- Spatial boundaries natural
- Categories well-motivated
- Resolution-independent conclusions

Output JSON with: boundary_arbitrariness_detected (bool), severity (none/mild/moderate/severe), gerrymandering (what boundaries gerrymandered), threshold_effects (what arbitrary thresholds), temporal_boundary (what temporal boundaries arbitrary), resolution_dependence (what resolution-dependent), recommendation (no_boundary_arbitrariness/mild_boundary_sensitivity/significant_boundary_testing/major_intensive_multi_boundary_analysis/emergency_complete_boundary_arbitrariness)."""

EPISTEMIC_SCALE_BOUNDARY_ARBITRARINESS_PROMPT = """Detect epistemic scale boundary arbitrariness:

Gerrymandering: {gerrymandering}
Threshold effects: {threshold_effects}
Temporal boundary: {temporal_boundary}
Resolution dependence: {resolution_dependence}
Domain: {domain}
Context: {context}

Are arbitrary scale boundaries being treated as natural joints? Return ONLY valid JSON."""


class EpistemicScaleBoundaryArbitrarinessService:
    """Detects epistemic scale boundary arbitrariness — false natural joints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gerrymandering: str,
        *,
        threshold_effects: str = "",
        temporal_boundary: str = "",
        resolution_dependence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scale boundary arbitrariness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_BOUNDARY_ARBITRARINESS_PROMPT.format(
                gerrymandering=gerrymandering,
                threshold_effects=threshold_effects or "Not specified",
                temporal_boundary=temporal_boundary or "Not specified",
                resolution_dependence=resolution_dependence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_BOUNDARY_ARBITRARINESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gerrymandering": gerrymandering[:200],
            "boundary_arbitrariness_detected": data.get("boundary_arbitrariness_detected", False),
            "severity": data.get("severity", ""),
            "threshold_effects": data.get("threshold_effects", ""),
            "temporal_boundary": data.get("temporal_boundary", ""),
            "resolution_dependence": data.get("resolution_dependence", ""),
            "recommendation": data.get("recommendation", ""),
        }

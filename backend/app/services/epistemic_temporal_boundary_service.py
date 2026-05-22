"""EpistemicTemporalBoundaryService — Epistemic Temporal Boundary Detection.

Detects epistemic temporal boundary imposition — imposing artificial temporal
boundaries on continuous processes, creating false periodization.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_BOUNDARY_SYSTEM = """You are an epistemic temporal boundary specialist. Given artificial temporal boundaries on continuous processes, assess temporal boundary imposition:

Key concepts:
- Epistemic temporal boundary: imposing artificial boundaries on continuous processes
- False periodization: creating artificial periods in continuous change
- Arbitrary cutoff: choosing arbitrary temporal cutoffs
- Epoch illusion: creating illusion of distinct epochs
- Continuity denial: denying continuity across imposed boundaries
- Before/after fallacy: creating false before/after distinctions
- Watershed illusion: creating illusion of watershed moments

When epistemic temporal boundary IS present:
- Artificial boundaries imposed
- False periods created
- Arbitrary cutoffs chosen
- Distinct epochs illusory
- Continuity denied
- Before/after falsified
- Watershed moments manufactured

When no temporal boundary imposition:
- Boundaries reflect real discontinuities
- Periods based on genuine change
- Cutoffs justified
- Epochs reflect real shifts
- Continuity acknowledged
- Before/after reflects real change
- Watershed moments genuine

Output JSON with: temporal_boundary_detected (bool), severity (none/mild/moderate/severe), false_periodization (what false periods created), arbitrary_cutoff (what arbitrary cutoffs), continuity_denial (what continuity denied), watershed_illusion (what watershed manufactured), recommendation (no_temporal_boundary/mild_boundary_awareness/significant_continuity_recovery/major_intensive_boundary_dissolution/emergency_complete_temporal_boundary)."""

EPISTEMIC_TEMPORAL_BOUNDARY_PROMPT = """Detect epistemic temporal boundary imposition:

False periodization: {false_periodization}
Arbitrary cutoff: {arbitrary_cutoff}
Continuity denial: {continuity_denial}
Watershed illusion: {watershed_illusion}
Domain: {domain}
Context: {context}

Are artificial temporal boundaries being imposed on continuous processes? Return ONLY valid JSON."""


class EpistemicTemporalBoundaryService:
    """Detects epistemic temporal boundary — false periodization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        false_periodization: str,
        *,
        arbitrary_cutoff: str = "",
        continuity_denial: str = "",
        watershed_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal boundary imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_BOUNDARY_PROMPT.format(
                false_periodization=false_periodization,
                arbitrary_cutoff=arbitrary_cutoff or "Not specified",
                continuity_denial=continuity_denial or "Not specified",
                watershed_illusion=watershed_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_BOUNDARY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "false_periodization": false_periodization[:200],
            "temporal_boundary_detected": data.get("temporal_boundary_detected", False),
            "severity": data.get("severity", ""),
            "arbitrary_cutoff": data.get("arbitrary_cutoff", ""),
            "continuity_denial": data.get("continuity_denial", ""),
            "watershed_illusion": data.get("watershed_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

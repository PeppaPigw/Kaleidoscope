"""EpistemicStrabismusService — Epistemic Strabismus Detection.

Detects epistemic strabismus — crossed eyes where two intellectual perspectives
point in different directions unable to converge on a single focus.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRABISMUS_SYSTEM = """You are an epistemic strabismus specialist. Given intellectual perspectives unable to converge, assess strabismus:

Key concepts:
- Epistemic strabismus: perspectives pointing different directions
- Esotropia: perspectives turning inward (over-convergence)
- Exotropia: perspectives turning outward (divergence)
- Fusion failure: inability to merge two views into one
- Prism correction: redirecting perspective alignment
- Surgery: structural realignment of perspective muscles
- Alternating: switching between perspectives rather than merging

When epistemic strabismus IS present:
- Two perspectives pointing different directions
- Unable to converge on single focus
- Fusion of views failing
- Over-convergence or divergence present
- Structural misalignment of perspective
- Alternating rather than integrating
- Double intellectual vision from misalignment

When no strabismus:
- Perspectives properly aligned
- Convergence on single focus achieved
- Views fusing successfully
- No over-convergence or divergence
- Structural alignment correct
- Integration rather than alternation
- Single unified intellectual vision

Output JSON with: strabismus_detected (bool), severity (none/mild/moderate/severe), deviation_type (what misalignment direction), convergence_status (what fusion ability), alternation_pattern (what switching), structural_cause (what underlying issue), recommendation (no_strabismus/mild_exercises/significant_prism_correction/major_surgical_realignment/emergency_acute_onset)."""

EPISTEMIC_STRABISMUS_PROMPT = """Detect epistemic strabismus:

Deviation type: {deviation_type}
Convergence status: {convergence_status}
Alternation pattern: {alternation_pattern}
Structural cause: {structural_cause}
Domain: {domain}
Context: {context}

Are two intellectual perspectives pointing in different directions unable to converge? Return ONLY valid JSON."""


class EpistemicStrabismusService:
    """Detects epistemic strabismus — perspectives unable to converge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deviation_type: str,
        *,
        convergence_status: str = "",
        alternation_pattern: str = "",
        structural_cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic strabismus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRABISMUS_PROMPT.format(
                deviation_type=deviation_type,
                convergence_status=convergence_status or "Not specified",
                alternation_pattern=alternation_pattern or "Not specified",
                structural_cause=structural_cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRABISMUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deviation_type": deviation_type[:200],
            "strabismus_detected": data.get("strabismus_detected", False),
            "severity": data.get("severity", ""),
            "convergence_status": data.get("convergence_status", ""),
            "alternation_pattern": data.get("alternation_pattern", ""),
            "structural_cause": data.get("structural_cause", ""),
            "recommendation": data.get("recommendation", ""),
        }

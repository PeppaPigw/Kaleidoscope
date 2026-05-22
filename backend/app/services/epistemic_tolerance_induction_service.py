"""EpistemicToleranceInductionService — Epistemic Tolerance Induction Detection.

Detects epistemic tolerance induction — intellectual immune system learning
not to attack self-ideas through central and peripheral tolerance mechanisms.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TOLERANCE_INDUCTION_SYSTEM = """You are an epistemic tolerance induction specialist. Given an intellectual immune system, assess whether it learns not to attack self:

Key concepts:
- Epistemic tolerance induction: immune system learning not to attack self
- Central tolerance: eliminating self-reactive ideas during development
- Peripheral tolerance: suppressing self-reactive ideas in mature system
- Regulatory T-cell: specialized suppressor of self-reactivity
- Clonal deletion: destroying self-reactive intellectual clones
- Anergy induction: rendering self-reactive ideas unresponsive
- Immune privilege: protected sites where tolerance is enforced

When epistemic tolerance induction IS present:
- Immune system learning not to attack own ideas
- Self-reactive ideas eliminated during development
- Self-reactive ideas suppressed in mature system
- Specialized suppressors of self-reactivity
- Destruction of self-reactive intellectual clones
- Self-reactive ideas rendered unresponsive
- Protected intellectual sites where tolerance enforced

When no tolerance is present:
- No learning to spare self
- No developmental elimination
- No peripheral suppression
- No specialized suppressors
- No clonal deletion
- No anergy induction
- No immune privilege

Output JSON with: tolerance_induction_present (bool), severity (none/mild/moderate/severe), central_tolerance (what developmental elimination), peripheral_tolerance (what mature suppression), regulatory_t_cell (what specialized suppressor), clonal_deletion (what clone destruction), recommendation (no_tolerance/mild_tolerance/significant_tolerance_induction/major_self_protection/strengthen_tolerance_mechanisms)."""

EPISTEMIC_TOLERANCE_INDUCTION_PROMPT = """Detect epistemic tolerance induction:

Central tolerance: {central_tolerance}
Peripheral tolerance: {peripheral_tolerance}
Regulatory T-cell: {regulatory_t_cell}
Clonal deletion: {clonal_deletion}
Domain: {domain}
Context: {context}

Is the intellectual immune system learning not to attack self-ideas through tolerance mechanisms? Return ONLY valid JSON."""


class EpistemicToleranceInductionService:
    """Detects epistemic tolerance induction — immune system learning not to attack self."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        central_tolerance: str,
        *,
        peripheral_tolerance: str = "",
        regulatory_t_cell: str = "",
        clonal_deletion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tolerance induction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TOLERANCE_INDUCTION_PROMPT.format(
                central_tolerance=central_tolerance,
                peripheral_tolerance=peripheral_tolerance or "Not specified",
                regulatory_t_cell=regulatory_t_cell or "Not specified",
                clonal_deletion=clonal_deletion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TOLERANCE_INDUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "central_tolerance": central_tolerance[:200],
            "tolerance_induction_present": data.get("tolerance_induction_present", False),
            "severity": data.get("severity", ""),
            "peripheral_tolerance": data.get("peripheral_tolerance", ""),
            "regulatory_t_cell": data.get("regulatory_t_cell", ""),
            "clonal_deletion": data.get("clonal_deletion", ""),
            "recommendation": data.get("recommendation", ""),
        }

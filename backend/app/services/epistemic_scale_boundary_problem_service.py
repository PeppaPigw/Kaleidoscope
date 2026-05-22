"""EpistemicScaleBoundaryProblemService - Epistemic Scale Boundary Problem Detection.

Detects boundary problem where arbitrary system boundaries distort analysis.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_BOUNDARY_PROBLEM_SYSTEM = """You are an epistemic scale boundary problem specialist. Given arbitrary boundary, assess boundary-driven distortion:

Key concepts:
- Epistemic scale boundary problem: arbitrary system boundaries distorting analysis
- Arbitrary boundary: system limits chosen without justification
- System definition bias: conclusions driven by how the system is defined
- Inclusion-exclusion distortion: important elements wrongly included or excluded
- Boundary effects ignored: interactions across the boundary overlooked

When boundary problem IS present:
- System boundaries are arbitrary
- System definition biases conclusions
- Inclusion and exclusion distort analysis
- Boundary effects are ignored
- Cross-boundary interactions are missed

When no boundary problem:
- Boundaries are justified
- System definition is explicit
- Inclusion and exclusion choices are tested
- Boundary effects are considered
- Cross-boundary interactions are examined

Output JSON with: boundary_problem_detected (bool), severity (none/mild/moderate/severe), system_definition_bias (what definition biases analysis), inclusion_exclusion_distortion (what inclusion or exclusion distorts), boundary_effects_ignored (what boundary effects are ignored), recommendation (no_boundary_problem/mild_boundary_check/significant_system_redefinition/major_boundary_sensitivity_analysis/emergency_complete_boundary_problem)."""

EPISTEMIC_SCALE_BOUNDARY_PROBLEM_PROMPT = """Detect epistemic scale boundary problem:

Arbitrary boundary: {arbitrary_boundary}
System definition bias: {system_definition_bias}
Inclusion-exclusion distortion: {inclusion_exclusion_distortion}
Boundary effects ignored: {boundary_effects_ignored}
Domain: {domain}
Context: {context}

Are arbitrary system boundaries distorting the analysis? Return ONLY valid JSON."""


class EpistemicScaleBoundaryProblemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arbitrary_boundary: str,
        *,
        system_definition_bias: str = "",
        inclusion_exclusion_distortion: str = "",
        boundary_effects_ignored: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_BOUNDARY_PROBLEM_PROMPT.format(
                arbitrary_boundary=arbitrary_boundary,
                system_definition_bias=system_definition_bias or "Not specified",
                inclusion_exclusion_distortion=inclusion_exclusion_distortion or "Not specified",
                boundary_effects_ignored=boundary_effects_ignored or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_BOUNDARY_PROBLEM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arbitrary_boundary": arbitrary_boundary[:200],
            "boundary_problem_detected": data.get("boundary_problem_detected", False),
            "severity": data.get("severity", ""),
            "system_definition_bias": data.get("system_definition_bias", ""),
            "inclusion_exclusion_distortion": data.get("inclusion_exclusion_distortion", ""),
            "boundary_effects_ignored": data.get("boundary_effects_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }

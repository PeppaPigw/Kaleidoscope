"""EpistemicScaleDivisionFallacyService - Epistemic Scale Division Fallacy Detection.

Detects division fallacy assuming what's true of whole is true of parts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_DIVISION_FALLACY_SYSTEM = """You are an epistemic scale division fallacy specialist. Given whole-to-part inference, assess division fallacy:

Key concepts:
- Epistemic scale division fallacy: assuming what is true of the whole is true of parts
- Whole-to-part inference: transferring aggregate properties to components
- Uniform distribution assumption: assuming whole-level properties distribute evenly
- Individual variation denial: ignoring variation among parts
- Average as universal: treating averages as true of every case

When division fallacy IS present:
- Whole properties are assigned to parts
- Uniform distribution is assumed
- Individual variation is denied
- Averages are treated as universal
- Scale transitions are ignored

When no division fallacy:
- Whole and part levels are distinguished
- Distribution is examined
- Individual variation is preserved
- Averages are contextualized
- Scale limits are acknowledged

Output JSON with: division_fallacy_detected (bool), severity (none/mild/moderate/severe), uniform_distribution_assumption (what uniformity is assumed), individual_variation_denial (what variation is denied), average_as_universal (what average is treated as universal), recommendation (no_division_fallacy/mild_distribution_check/significant_heterogeneity_analysis/major_individual_level_reconstruction/emergency_complete_division_fallacy)."""

EPISTEMIC_SCALE_DIVISION_FALLACY_PROMPT = """Detect epistemic scale division fallacy:

Whole-to-part inference: {whole_to_part_inference}
Uniform distribution assumption: {uniform_distribution_assumption}
Individual variation denial: {individual_variation_denial}
Average as universal: {average_as_universal}
Domain: {domain}
Context: {context}

Is what is true of the whole being assumed true of parts? Return ONLY valid JSON."""


class EpistemicScaleDivisionFallacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        whole_to_part_inference: str,
        *,
        uniform_distribution_assumption: str = "",
        individual_variation_denial: str = "",
        average_as_universal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_DIVISION_FALLACY_PROMPT.format(
                whole_to_part_inference=whole_to_part_inference,
                uniform_distribution_assumption=uniform_distribution_assumption or "Not specified",
                individual_variation_denial=individual_variation_denial or "Not specified",
                average_as_universal=average_as_universal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_DIVISION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "whole_to_part_inference": whole_to_part_inference[:200],
            "division_fallacy_detected": data.get("division_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "uniform_distribution_assumption": data.get("uniform_distribution_assumption", ""),
            "individual_variation_denial": data.get("individual_variation_denial", ""),
            "average_as_universal": data.get("average_as_universal", ""),
            "recommendation": data.get("recommendation", ""),
        }

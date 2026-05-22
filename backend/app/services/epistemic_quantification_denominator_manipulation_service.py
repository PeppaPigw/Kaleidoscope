"""EpistemicQuantificationDenominatorManipulationService — Epistemic Denominator Manipulation Detection.

Detects epistemic quantification denominator manipulation — manipulating
denominators to distort rates, proportions, and comparisons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTIFICATION_DENOMINATOR_MANIPULATION_SYSTEM = """You are an epistemic quantification denominator manipulation specialist. Given denominator manipulation, assess rate distortion:

Key concepts:
- Epistemic denominator manipulation: manipulating denominators to distort rates
- Base rate manipulation: choosing denominators that inflate or deflate rates
- Population switching: switching between populations to change denominators
- Temporal denominator shift: changing time periods to manipulate rates
- Selective inclusion: including/excluding from denominator to change rates
- Denominator suppression: presenting numerators without denominators
- Rate vs count confusion: switching between rates and counts strategically

When epistemic denominator manipulation IS present:
- Denominators manipulated to distort rates
- Base rates manipulated
- Populations switched
- Time periods shifted
- Selective inclusion/exclusion
- Denominators suppressed
- Rate/count confusion exploited

When no denominator manipulation:
- Denominators appropriate and transparent
- Base rates honest
- Populations consistent
- Time periods appropriate
- Inclusion criteria clear
- Denominators stated
- Rate/count distinction maintained

Output JSON with: denominator_manipulation_detected (bool), severity (none/mild/moderate/severe), base_rate_manipulation (what base rates manipulated), population_switching (what populations switched), denominator_suppression (what denominators suppressed), rate_count_confusion (what rate/count confusion), recommendation (no_denominator_manipulation/mild_denominator_transparency/significant_rate_recalculation/major_intensive_denominator_audit/emergency_complete_denominator_manipulation)."""

EPISTEMIC_QUANTIFICATION_DENOMINATOR_MANIPULATION_PROMPT = """Detect epistemic quantification denominator manipulation:

Base rate manipulation: {base_rate_manipulation}
Population switching: {population_switching}
Denominator suppression: {denominator_suppression}
Rate count confusion: {rate_count_confusion}
Domain: {domain}
Context: {context}

Are denominators being manipulated to distort rates and proportions? Return ONLY valid JSON."""


class EpistemicQuantificationDenominatorManipulationService:
    """Detects epistemic denominator manipulation — rate distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        base_rate_manipulation: str,
        *,
        population_switching: str = "",
        denominator_suppression: str = "",
        rate_count_confusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantification denominator manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTIFICATION_DENOMINATOR_MANIPULATION_PROMPT.format(
                base_rate_manipulation=base_rate_manipulation,
                population_switching=population_switching or "Not specified",
                denominator_suppression=denominator_suppression or "Not specified",
                rate_count_confusion=rate_count_confusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTIFICATION_DENOMINATOR_MANIPULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "base_rate_manipulation": base_rate_manipulation[:200],
            "denominator_manipulation_detected": data.get("denominator_manipulation_detected", False),
            "severity": data.get("severity", ""),
            "population_switching": data.get("population_switching", ""),
            "denominator_suppression": data.get("denominator_suppression", ""),
            "rate_count_confusion": data.get("rate_count_confusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

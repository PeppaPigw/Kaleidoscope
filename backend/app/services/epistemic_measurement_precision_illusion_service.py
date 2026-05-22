"""EpistemicMeasurementPrecisionIllusionService — Epistemic Measurement Precision Illusion Detection.

Detects epistemic measurement precision illusion — false precision in
measurements that masks underlying uncertainty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEASUREMENT_PRECISION_ILLUSION_SYSTEM = """You are an epistemic measurement precision illusion specialist. Given false precision, assess whether measurements mask underlying uncertainty:

Key concepts:
- False precision: numerical specificity exceeds actual measurement reliability
- Significant figures abuse: reporting more digits than the evidence supports
- Measurement error hiding: uncertainty, noise, or instrument limits are suppressed
- Confidence interval neglect: point estimates are treated as exact values

When precision illusion IS present:
- Exact numbers imply unjustified certainty
- Extra digits conceal uncertain estimates
- Measurement error is omitted or minimized
- Confidence intervals are missing or ignored
- Decisions overinterpret small numerical differences

When no precision illusion:
- Precision matches measurement reliability
- Significant figures reflect uncertainty
- Error bounds are disclosed
- Confidence intervals guide interpretation
- Numerical differences are evaluated against uncertainty

Output JSON with: precision_illusion_detected (bool), severity (none/mild/moderate/severe), false_precision (what false precision appears), significant_figures_abuse (what digits overstate precision), measurement_error_hiding (what uncertainty is hidden), confidence_interval_neglect (what intervals are ignored), recommendation (no_precision_illusion/mild_uncertainty_labeling/significant_error_disclosure/major_measurement_reframing/emergency_precision_claim_retraction)."""

EPISTEMIC_MEASUREMENT_PRECISION_ILLUSION_PROMPT = """Detect epistemic measurement precision illusion:

False precision: {false_precision}
Significant figures abuse: {significant_figures_abuse}
Measurement error hiding: {measurement_error_hiding}
Confidence interval neglect: {confidence_interval_neglect}
Domain: {domain}
Context: {context}

Are measurements showing false precision that masks underlying uncertainty? Return ONLY valid JSON."""


class EpistemicMeasurementPrecisionIllusionService:
    """Detects epistemic measurement precision illusion — false precision."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        false_precision: str,
        *,
        significant_figures_abuse: str = "",
        measurement_error_hiding: str = "",
        confidence_interval_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic measurement precision illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEASUREMENT_PRECISION_ILLUSION_PROMPT.format(
                false_precision=false_precision,
                significant_figures_abuse=significant_figures_abuse or "Not specified",
                measurement_error_hiding=measurement_error_hiding or "Not specified",
                confidence_interval_neglect=confidence_interval_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEASUREMENT_PRECISION_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "false_precision": false_precision[:200],
            "precision_illusion_detected": data.get("precision_illusion_detected", False),
            "severity": data.get("severity", ""),
            "significant_figures_abuse": data.get("significant_figures_abuse", ""),
            "measurement_error_hiding": data.get("measurement_error_hiding", ""),
            "confidence_interval_neglect": data.get("confidence_interval_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }

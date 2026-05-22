"""EpistemicQuantificationFalsePrecisionService — Epistemic False Precision Detection.

Detects epistemic quantification false precision — presenting imprecise
knowledge with false numerical precision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTIFICATION_FALSE_PRECISION_SYSTEM = """You are an epistemic quantification false precision specialist. Given false precision in quantification, assess precision distortion:

Key concepts:
- Epistemic false precision: presenting imprecise knowledge with false numerical precision
- Spurious decimal places: reporting more decimal places than data supports
- False confidence intervals: presenting narrow intervals when uncertainty is wide
- Precision without accuracy: precise numbers that aren't accurate
- Measurement theater: performing precise measurement on imprecise concepts
- Significant figure inflation: reporting more significant figures than warranted
- Pseudo-quantification: assigning numbers to inherently qualitative phenomena

When epistemic false precision IS present:
- Imprecise knowledge presented precisely
- Spurious decimal places reported
- Confidence intervals falsely narrow
- Precision without accuracy
- Measurement theater performed
- Significant figures inflated
- Qualitative phenomena pseudo-quantified

When no false precision:
- Precision matches underlying uncertainty
- Decimal places appropriate
- Confidence intervals honest
- Precision and accuracy aligned
- Measurement genuine
- Significant figures warranted
- Quantification appropriate

Output JSON with: false_precision_detected (bool), severity (none/mild/moderate/severe), spurious_decimals (what spurious precision), false_confidence_intervals (what false intervals), measurement_theater (what measurement theater), pseudo_quantification (what pseudo-quantified), recommendation (no_false_precision/mild_uncertainty_acknowledgment/significant_precision_reduction/major_intensive_uncertainty_communication/emergency_complete_false_precision)."""

EPISTEMIC_QUANTIFICATION_FALSE_PRECISION_PROMPT = """Detect epistemic quantification false precision:

Spurious decimals: {spurious_decimals}
False confidence intervals: {false_confidence_intervals}
Measurement theater: {measurement_theater}
Pseudo quantification: {pseudo_quantification}
Domain: {domain}
Context: {context}

Is imprecise knowledge being presented with false numerical precision? Return ONLY valid JSON."""


class EpistemicQuantificationFalsePrecisionService:
    """Detects epistemic false precision — precision beyond data support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        spurious_decimals: str,
        *,
        false_confidence_intervals: str = "",
        measurement_theater: str = "",
        pseudo_quantification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantification false precision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTIFICATION_FALSE_PRECISION_PROMPT.format(
                spurious_decimals=spurious_decimals,
                false_confidence_intervals=false_confidence_intervals or "Not specified",
                measurement_theater=measurement_theater or "Not specified",
                pseudo_quantification=pseudo_quantification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTIFICATION_FALSE_PRECISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "spurious_decimals": spurious_decimals[:200],
            "false_precision_detected": data.get("false_precision_detected", False),
            "severity": data.get("severity", ""),
            "false_confidence_intervals": data.get("false_confidence_intervals", ""),
            "measurement_theater": data.get("measurement_theater", ""),
            "pseudo_quantification": data.get("pseudo_quantification", ""),
            "recommendation": data.get("recommendation", ""),
        }

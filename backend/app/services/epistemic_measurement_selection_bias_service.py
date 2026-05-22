"""EpistemicMeasurementSelectionBiasService — Epistemic Measurement Selection Bias Detection.

Detects epistemic measurement selection bias — selection bias in what gets
measured and reported.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEASUREMENT_SELECTION_BIAS_SYSTEM = """You are an epistemic measurement selection bias specialist. Given measurement selection, assess whether selection bias affects what gets measured and reported:

Key concepts:
- Measurement selection: measured cases, variables, or outcomes are not representative of the relevant reality
- Survivorship in data: failed, absent, or missing cases are excluded from measurement
- Publication bias: reported findings overrepresent positive, significant, or interesting results
- Reporting asymmetry: favorable or available measurements are reported more than unfavorable or missing ones

When measurement selection bias IS present:
- Measured cases differ systematically from unmeasured cases
- Survivors are mistaken for the full population
- Null or negative findings are underreported
- Reporting favors convenient or favorable data
- Conclusions generalize beyond the measured sample

When no measurement selection bias:
- Measurement coverage is representative or bounded
- Missing and failed cases are considered
- Reporting includes null and negative evidence
- Inclusion criteria are explicit
- Conclusions respect measurement limits

Output JSON with: measurement_selection_bias_detected (bool), severity (none/mild/moderate/severe), measurement_selection (what selection process biases measurement), survivorship_in_data (what missing survivors/non-survivors distort), publication_bias (what reporting bias exists), reporting_asymmetry (what asymmetric reporting occurs), recommendation (no_selection_bias/mild_coverage_note/significant_missing_case_analysis/major_sampling_redesign/emergency_claim_withdrawal)."""

EPISTEMIC_MEASUREMENT_SELECTION_BIAS_PROMPT = """Detect epistemic measurement selection bias:

Measurement selection: {measurement_selection}
Survivorship in data: {survivorship_in_data}
Publication bias: {publication_bias}
Reporting asymmetry: {reporting_asymmetry}
Domain: {domain}
Context: {context}

Is selection bias affecting what gets measured and reported? Return ONLY valid JSON."""


class EpistemicMeasurementSelectionBiasService:
    """Detects epistemic measurement selection bias — biased measurement coverage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        measurement_selection: str,
        *,
        survivorship_in_data: str = "",
        publication_bias: str = "",
        reporting_asymmetry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic measurement selection bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEASUREMENT_SELECTION_BIAS_PROMPT.format(
                measurement_selection=measurement_selection,
                survivorship_in_data=survivorship_in_data or "Not specified",
                publication_bias=publication_bias or "Not specified",
                reporting_asymmetry=reporting_asymmetry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEASUREMENT_SELECTION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "measurement_selection": measurement_selection[:200],
            "measurement_selection_bias_detected": data.get("measurement_selection_bias_detected", False),
            "severity": data.get("severity", ""),
            "survivorship_in_data": data.get("survivorship_in_data", ""),
            "publication_bias": data.get("publication_bias", ""),
            "reporting_asymmetry": data.get("reporting_asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }

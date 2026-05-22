"""EpistemicMeasurementAggregationDistortionService — Epistemic Measurement Aggregation Distortion Detection.

Detects epistemic measurement aggregation distortion — how aggregation of
measurements distorts understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEASUREMENT_AGGREGATION_DISTORTION_SYSTEM = """You are an epistemic measurement aggregation distortion specialist. Given Simpson paradox risk, assess whether aggregation of measurements distorts understanding:

Key concepts:
- Simpson paradox risk: aggregate trends may reverse or obscure subgroup trends
- Ecological fallacy: aggregate-level measurements are incorrectly applied to individuals or subgroups
- Averaging artifacts: means or summary statistics conceal meaningful variation
- Distribution collapse: distributions are reduced to aggregates that erase spread, tails, or multimodality

When aggregation distortion IS present:
- Aggregate metrics hide subgroup differences
- Overall trends reverse subgroup patterns
- Group-level results are projected onto individuals
- Averages conceal outliers, tails, or multimodal structure
- Decisions rely on summaries without distributional checks

When no aggregation distortion:
- Subgroup and aggregate trends are compared
- Individual and group-level claims are separated
- Distributional shape is inspected
- Summary statistics are contextualized
- Aggregation choices are justified

Output JSON with: aggregation_distortion_detected (bool), severity (none/mild/moderate/severe), simpson_paradox_risk (what aggregate/subgroup reversal risk exists), ecological_fallacy (what aggregate-to-individual inference occurs), averaging_artifacts (what averages conceal), distribution_collapse (what distributional information is lost), recommendation (no_aggregation_distortion/mild_subgroup_check/significant_distribution_review/major_disaggregation_required/emergency_aggregate_claim_retraction)."""

EPISTEMIC_MEASUREMENT_AGGREGATION_DISTORTION_PROMPT = """Detect epistemic measurement aggregation distortion:

Simpson paradox risk: {simpson_paradox_risk}
Ecological fallacy: {ecological_fallacy}
Averaging artifacts: {averaging_artifacts}
Distribution collapse: {distribution_collapse}
Domain: {domain}
Context: {context}

Is aggregation of measurements distorting understanding? Return ONLY valid JSON."""


class EpistemicMeasurementAggregationDistortionService:
    """Detects epistemic measurement aggregation distortion — aggregation artifacts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        simpson_paradox_risk: str,
        *,
        ecological_fallacy: str = "",
        averaging_artifacts: str = "",
        distribution_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic measurement aggregation distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEASUREMENT_AGGREGATION_DISTORTION_PROMPT.format(
                simpson_paradox_risk=simpson_paradox_risk,
                ecological_fallacy=ecological_fallacy or "Not specified",
                averaging_artifacts=averaging_artifacts or "Not specified",
                distribution_collapse=distribution_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEASUREMENT_AGGREGATION_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "simpson_paradox_risk": simpson_paradox_risk[:200],
            "aggregation_distortion_detected": data.get("aggregation_distortion_detected", False),
            "severity": data.get("severity", ""),
            "ecological_fallacy": data.get("ecological_fallacy", ""),
            "averaging_artifacts": data.get("averaging_artifacts", ""),
            "distribution_collapse": data.get("distribution_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }

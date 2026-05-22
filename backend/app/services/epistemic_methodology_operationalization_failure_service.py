"""EpistemicMethodologyOperationalizationFailureService - Epistemic Methodology Operationalization Failure Detection.

Detects operationalization failure where measurement doesn't capture intended construct.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METHODOLOGY_OPERATIONALIZATION_FAILURE_SYSTEM = """You are an epistemic methodology operationalization failure specialist. Given construct-measurement gap, assess operationalization failure:

Key concepts:
- Epistemic methodology operationalization failure: measurement does not capture the intended construct
- Construct-measurement gap: distance between concept and measured indicator
- Validity threat: measurement undermines valid inference
- Indicator inadequacy: chosen indicator fails to represent the construct
- Conceptual slippage: concept shifts during measurement or interpretation

When operationalization failure IS present:
- Measurement misses the intended construct
- Validity is threatened
- Indicators are inadequate
- Concepts slip during analysis
- Conclusions exceed what measurement supports

When no operationalization failure:
- Measures align with constructs
- Validity threats are addressed
- Indicators are adequate
- Concepts remain stable
- Conclusions match measurement limits

Output JSON with: operationalization_failure_detected (bool), severity (none/mild/moderate/severe), validity_threat (what validity threat appears), indicator_inadequacy (what indicator is inadequate), conceptual_slippage (what concept slips), recommendation (no_operationalization_failure/mild_validity_check/significant_measure_revision/major_construct_reassessment/emergency_complete_operationalization_failure)."""

EPISTEMIC_METHODOLOGY_OPERATIONALIZATION_FAILURE_PROMPT = """Detect epistemic methodology operationalization failure:

Construct-measurement gap: {construct_measurement_gap}
Validity threat: {validity_threat}
Indicator inadequacy: {indicator_inadequacy}
Conceptual slippage: {conceptual_slippage}
Domain: {domain}
Context: {context}

Does the measurement fail to capture the intended construct? Return ONLY valid JSON."""


class EpistemicMethodologyOperationalizationFailureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        construct_measurement_gap: str,
        *,
        validity_threat: str = "",
        indicator_inadequacy: str = "",
        conceptual_slippage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METHODOLOGY_OPERATIONALIZATION_FAILURE_PROMPT.format(
                construct_measurement_gap=construct_measurement_gap,
                validity_threat=validity_threat or "Not specified",
                indicator_inadequacy=indicator_inadequacy or "Not specified",
                conceptual_slippage=conceptual_slippage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METHODOLOGY_OPERATIONALIZATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "construct_measurement_gap": construct_measurement_gap[:200],
            "operationalization_failure_detected": data.get("operationalization_failure_detected", False),
            "severity": data.get("severity", ""),
            "validity_threat": data.get("validity_threat", ""),
            "indicator_inadequacy": data.get("indicator_inadequacy", ""),
            "conceptual_slippage": data.get("conceptual_slippage", ""),
            "recommendation": data.get("recommendation", ""),
        }

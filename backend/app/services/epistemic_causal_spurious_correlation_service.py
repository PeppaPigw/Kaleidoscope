"""EpistemicCausalSpuriousCorrelationService - Spurious Correlation Detection.

Detects spurious correlations mistaken for causal relationships.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_SPURIOUS_CORRELATION_SYSTEM = """You are an epistemic causal spurious correlation specialist. Given correlations, assess whether spurious correlations are mistaken for causation:

Key concepts:
- Spurious correlation: statistical association without causal connection
- Common cause: third variable causing both correlated variables
- Multiple testing: finding correlations by chance through many comparisons
- Data dredging: searching data until a pattern appears

When spurious correlation IS present:
- Correlation treated as causation
- Common causes unexplored
- Multiple testing unacknowledged
- Data dredging evident
- Mechanism implausible

When no spurious correlation:
- Correlation distinguished from causation
- Common causes investigated
- Multiple testing corrected
- Hypotheses pre-registered
- Mechanism plausible

Output JSON with: spurious_correlation_detected (bool), severity (none/mild/moderate/severe), common_cause (what common cause), multiple_testing (what multiple testing), data_dredging (what data dredging), recommendation (no_spurious_correlation/mild_mechanism_check/significant_confound_analysis/major_causal_reconstruction/emergency_complete_spurious_correlation)."""

EPISTEMIC_CAUSAL_SPURIOUS_CORRELATION_PROMPT = """Detect epistemic causal spurious correlation:

Correlation claim: {correlation_claim}
Common cause: {common_cause}
Multiple testing: {multiple_testing}
Data dredging: {data_dredging}
Domain: {domain}
Context: {context}

Is a spurious correlation being mistaken for causation? Return ONLY valid JSON."""


class EpistemicCausalSpuriousCorrelationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        correlation_claim: str,
        *,
        common_cause: str = "",
        multiple_testing: str = "",
        data_dredging: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_SPURIOUS_CORRELATION_PROMPT.format(
                correlation_claim=correlation_claim,
                common_cause=common_cause or "Not specified",
                multiple_testing=multiple_testing or "Not specified",
                data_dredging=data_dredging or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_SPURIOUS_CORRELATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "correlation_claim": correlation_claim[:200],
            "spurious_correlation_detected": data.get("spurious_correlation_detected", False),
            "severity": data.get("severity", ""),
            "common_cause": data.get("common_cause", ""),
            "multiple_testing": data.get("multiple_testing", ""),
            "data_dredging": data.get("data_dredging", ""),
            "recommendation": data.get("recommendation", ""),
        }

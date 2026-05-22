"""FalsePrecisionService — False Precision Detection.

Detects false precision — using specific numbers, decimal places,
or exact figures to create an illusion of accuracy when the
underlying data or methodology doesn't support that level of
precision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_PRECISION_SYSTEM = """You are a false precision specialist. Given a claim with specific numbers, assess whether the precision is warranted:

Key concepts:
- False precision: specific numbers implying accuracy that doesn't exist
- Significant figures: more digits than the measurement supports
- Spurious accuracy: calculations producing precise results from imprecise inputs
- Precision vs accuracy: precise doesn't mean correct
- Confidence intervals: what range the true value likely falls in
- Measurement uncertainty: inherent limits of the measurement
- Anchoring through precision: specific numbers anchor more than ranges

When false precision IS present:
- Specific numbers given without uncertainty ranges
- More decimal places than the data supports
- Precise calculations from imprecise inputs
- Exact figures for inherently uncertain quantities
- Surveys or estimates reported to false decimal places
- Projections stated as exact numbers rather than ranges
- Precision used to create appearance of rigor

When false precision is NOT present:
- Precision matches measurement capability
- Uncertainty ranges provided alongside point estimates
- Appropriate significant figures used
- Inherent uncertainty acknowledged
- Ranges used for uncertain quantities
- Precision justified by methodology
- Numbers rounded appropriately for the context

Output JSON with: false_precision_present (bool), severity (none/mild/moderate/severe), claim (what is stated precisely), actual_uncertainty (what the real uncertainty is), precision_level (how precise the claim is), warranted_precision (what precision is justified), recommendation (appropriate_precision/mild_over_precision/significant_false_precision/major_spurious_accuracy/use_ranges)."""

FALSE_PRECISION_PROMPT = """Detect false precision:

Claim: {claim}
Number given: {number}
Data source: {source}
Methodology: {methodology}
Domain: {domain}
Context: {context}

Is the precision of these numbers warranted by the underlying data? Return ONLY valid JSON."""


class FalsePrecisionService:
    """Detects false precision — unwarranted specificity in numbers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        number: str = "",
        source: str = "",
        methodology: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false precision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_PRECISION_PROMPT.format(
                claim=claim,
                number=number or "Not specified",
                source=source or "Not specified",
                methodology=methodology or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_PRECISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "false_precision_present": data.get("false_precision_present", False),
            "severity": data.get("severity", ""),
            "actual_uncertainty": data.get("actual_uncertainty", ""),
            "precision_level": data.get("precision_level", ""),
            "warranted_precision": data.get("warranted_precision", ""),
            "recommendation": data.get("recommendation", ""),
        }

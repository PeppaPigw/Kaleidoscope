"""EpistemicQuantificationAggregationFallacyService — Epistemic Aggregation Fallacy Detection.

Detects epistemic quantification aggregation fallacy — aggregating data in ways
that hide important variation or create misleading summaries.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTIFICATION_AGGREGATION_FALLACY_SYSTEM = """You are an epistemic quantification aggregation fallacy specialist. Given misleading aggregation, assess aggregation distortion:

Key concepts:
- Epistemic aggregation fallacy: aggregating data to hide important variation
- Simpson's paradox exploitation: aggregation reversing relationships
- Mean masking: using means to hide bimodal or skewed distributions
- Subgroup erasure: aggregation erasing important subgroup differences
- Temporal aggregation: aggregating across time periods to hide trends
- Geographic aggregation: aggregating across regions to hide local variation
- Category lumping: lumping distinct categories to create misleading totals

When epistemic aggregation fallacy IS present:
- Important variation hidden by aggregation
- Simpson's paradox exploited
- Means masking distributions
- Subgroups erased
- Temporal trends hidden
- Geographic variation hidden
- Categories inappropriately lumped

When no aggregation fallacy:
- Aggregation preserves important variation
- Subgroups examined
- Distributions shown not just means
- Temporal patterns preserved
- Geographic variation acknowledged
- Categories appropriately defined
- Disaggregation available

Output JSON with: aggregation_fallacy_detected (bool), severity (none/mild/moderate/severe), mean_masking (what means mask), subgroup_erasure (what subgroups erased), temporal_aggregation (what temporal trends hidden), category_lumping (what categories lumped), recommendation (no_aggregation_fallacy/mild_disaggregation/significant_subgroup_analysis/major_intensive_distribution_examination/emergency_complete_aggregation_fallacy)."""

EPISTEMIC_QUANTIFICATION_AGGREGATION_FALLACY_PROMPT = """Detect epistemic quantification aggregation fallacy:

Mean masking: {mean_masking}
Subgroup erasure: {subgroup_erasure}
Temporal aggregation: {temporal_aggregation}
Category lumping: {category_lumping}
Domain: {domain}
Context: {context}

Is data being aggregated in ways that hide important variation? Return ONLY valid JSON."""


class EpistemicQuantificationAggregationFallacyService:
    """Detects epistemic aggregation fallacy — variation hidden by aggregation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mean_masking: str,
        *,
        subgroup_erasure: str = "",
        temporal_aggregation: str = "",
        category_lumping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantification aggregation fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTIFICATION_AGGREGATION_FALLACY_PROMPT.format(
                mean_masking=mean_masking,
                subgroup_erasure=subgroup_erasure or "Not specified",
                temporal_aggregation=temporal_aggregation or "Not specified",
                category_lumping=category_lumping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTIFICATION_AGGREGATION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mean_masking": mean_masking[:200],
            "aggregation_fallacy_detected": data.get("aggregation_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "subgroup_erasure": data.get("subgroup_erasure", ""),
            "temporal_aggregation": data.get("temporal_aggregation", ""),
            "category_lumping": data.get("category_lumping", ""),
            "recommendation": data.get("recommendation", ""),
        }

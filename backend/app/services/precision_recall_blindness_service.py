"""PrecisionRecallBlindnessService — Precision-Recall Tradeoff Blindness Detection.

Detects precision-recall tradeoff blindness — not recognizing that
increasing precision necessarily decreases recall and vice versa,
demanding both simultaneously without acknowledging the tradeoff.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRECISION_RECALL_BLINDNESS_SYSTEM = """You are a precision-recall tradeoff specialist. Given a classification or detection system, assess whether the precision-recall tradeoff is being ignored:

Key concepts:
- Precision-recall tradeoff: improving one typically worsens the other
- False positive aversion: demanding zero false positives (high precision)
- False negative aversion: demanding zero misses (high recall)
- Threshold blindness: not recognizing threshold choice creates tradeoff
- Having it both ways: demanding perfect precision AND recall
- Base rate interaction: how prevalence affects the tradeoff
- Operating point: where on the curve you choose to operate

When precision-recall blindness IS present:
- Both perfect precision and recall demanded simultaneously
- Tradeoff not acknowledged in system design
- Threshold choice not recognized as value judgment
- False positives condemned without noting false negative cost
- False negatives condemned without noting false positive cost
- System evaluated on one metric while other degrades
- Impossible standard applied (zero errors of both types)

When tradeoff management is appropriate:
- Tradeoff explicitly acknowledged
- Operating point chosen deliberately
- Costs of both error types weighed
- Threshold reflects value judgment about error costs
- Neither metric optimized at expense of other without justification
- Base rate effects considered
- Tradeoff communicated to stakeholders

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), system (what system is evaluated), precision_demand (what precision is demanded), recall_demand (what recall is demanded), tradeoff_ignored (what tradeoff is ignored), recommendation (appropriate_tradeoff_management/mild_metric_focus/significant_tradeoff_blindness/major_impossible_standard/acknowledge_tradeoff)."""

PRECISION_RECALL_BLINDNESS_PROMPT = """Detect precision-recall tradeoff blindness:

System: {system}
Requirements: {requirements}
Error tolerance: {tolerance}
Evaluation: {evaluation}
Domain: {domain}
Context: {context}

Is the precision-recall tradeoff being ignored or both demanded simultaneously? Return ONLY valid JSON."""


class PrecisionRecallBlindnessService:
    """Detects precision-recall tradeoff blindness — ignoring the fundamental tradeoff."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        requirements: str = "",
        tolerance: str = "",
        evaluation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect precision-recall tradeoff blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRECISION_RECALL_BLINDNESS_PROMPT.format(
                system=system,
                requirements=requirements or "Not specified",
                tolerance=tolerance or "Not specified",
                evaluation=evaluation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRECISION_RECALL_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "precision_demand": data.get("precision_demand", ""),
            "recall_demand": data.get("recall_demand", ""),
            "tradeoff_ignored": data.get("tradeoff_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }

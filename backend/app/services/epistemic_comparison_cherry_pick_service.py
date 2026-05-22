"""EpistemicComparisonCherryPickService — Epistemic Comparison Cherry-Pick Detection.

Detects epistemic comparison cherry-picking — cherry-picking comparison
points to support a predetermined conclusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARISON_CHERRY_PICK_SYSTEM = """You are an epistemic comparison cherry-pick specialist. Given cherry-picked comparisons, assess comparison cherry-picking:

Key concepts:
- Epistemic comparison cherry-pick: selecting comparison points to support conclusion
- Endpoint selection: choosing start/end points to show desired trend
- Comparator selection: choosing comparator to make subject look good/bad
- Dimension selection: choosing dimension that favors desired conclusion
- Time period selection: choosing time period that supports narrative
- Sample selection: selecting which cases to compare
- Metric selection: choosing metric that favors desired outcome

When epistemic comparison cherry-pick IS present:
- Comparison points selected to support conclusion
- Endpoints chosen strategically
- Comparators chosen to flatter/diminish
- Dimensions chosen selectively
- Time periods chosen strategically
- Cases selected to support
- Metrics chosen to favor

When no comparison cherry-picking:
- Comparison points representative
- Endpoints justified
- Comparators appropriate
- Dimensions comprehensive
- Time periods appropriate
- Cases representative
- Metrics appropriate

Output JSON with: comparison_cherry_pick_detected (bool), severity (none/mild/moderate/severe), endpoint_selection (what endpoints chosen), comparator_selection (what comparators chosen), dimension_selection (what dimensions chosen), time_period_selection (what time periods chosen), recommendation (no_comparison_cherry_pick/mild_selection_awareness/significant_representativeness_checking/major_intensive_comparison_broadening/emergency_complete_comparison_cherry_pick)."""

EPISTEMIC_COMPARISON_CHERRY_PICK_PROMPT = """Detect epistemic comparison cherry-picking:

Endpoint selection: {endpoint_selection}
Comparator selection: {comparator_selection}
Dimension selection: {dimension_selection}
Time period selection: {time_period_selection}
Domain: {domain}
Context: {context}

Are comparison points being cherry-picked to support a conclusion? Return ONLY valid JSON."""


class EpistemicComparisonCherryPickService:
    """Detects epistemic comparison cherry-pick — selective comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        endpoint_selection: str,
        *,
        comparator_selection: str = "",
        dimension_selection: str = "",
        time_period_selection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic comparison cherry-picking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARISON_CHERRY_PICK_PROMPT.format(
                endpoint_selection=endpoint_selection,
                comparator_selection=comparator_selection or "Not specified",
                dimension_selection=dimension_selection or "Not specified",
                time_period_selection=time_period_selection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARISON_CHERRY_PICK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "endpoint_selection": endpoint_selection[:200],
            "comparison_cherry_pick_detected": data.get("comparison_cherry_pick_detected", False),
            "severity": data.get("severity", ""),
            "comparator_selection": data.get("comparator_selection", ""),
            "dimension_selection": data.get("dimension_selection", ""),
            "time_period_selection": data.get("time_period_selection", ""),
            "recommendation": data.get("recommendation", ""),
        }

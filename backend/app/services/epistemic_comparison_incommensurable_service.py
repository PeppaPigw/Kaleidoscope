"""EpistemicComparisonIncommensurableService — Epistemic Incommensurable Comparison Detection.

Detects epistemic incommensurable comparison — comparing things that lack
a common metric as if they share one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARISON_INCOMMENSURABLE_SYSTEM = """You are an epistemic incommensurable comparison specialist. Given comparisons of incommensurable things, assess incommensurability:

Key concepts:
- Epistemic incommensurable comparison: comparing things without common metric
- Apples and oranges: comparing fundamentally different kinds
- Forced commensuration: forcing common metric on incommensurable values
- Dimension reduction: reducing multidimensional to single dimension for comparison
- Value pluralism denial: denying that values may be genuinely incommensurable
- Ranking the unrankable: ranking things that cannot be meaningfully ranked
- Metric imposition: imposing metric where none naturally exists

When epistemic incommensurable comparison IS present:
- Incommensurable things compared
- Apples compared with oranges
- Common metric forced
- Dimensions reduced
- Value pluralism denied
- Unrankable ranked
- Metrics imposed

When no incommensurable comparison:
- Comparisons appropriate
- Like compared with like
- Metrics natural
- Dimensions preserved
- Value pluralism acknowledged
- Rankings meaningful
- Metrics appropriate

Output JSON with: incommensurable_comparison_detected (bool), severity (none/mild/moderate/severe), forced_commensuration (what commensuration forced), dimension_reduction (what dimensions reduced), value_pluralism_denial (what pluralism denied), metric_imposition (what metrics imposed), recommendation (no_incommensurable_comparison/mild_commensurability_checking/significant_dimension_preservation/major_intensive_comparison_restructuring/emergency_complete_incommensurable_comparison)."""

EPISTEMIC_COMPARISON_INCOMMENSURABLE_PROMPT = """Detect epistemic incommensurable comparison:

Forced commensuration: {forced_commensuration}
Dimension reduction: {dimension_reduction}
Value pluralism denial: {value_pluralism_denial}
Metric imposition: {metric_imposition}
Domain: {domain}
Context: {context}

Are incommensurable things being compared as if they share a common metric? Return ONLY valid JSON."""


class EpistemicComparisonIncommensurableService:
    """Detects epistemic incommensurable comparison — forced metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        forced_commensuration: str,
        *,
        dimension_reduction: str = "",
        value_pluralism_denial: str = "",
        metric_imposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic incommensurable comparison."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARISON_INCOMMENSURABLE_PROMPT.format(
                forced_commensuration=forced_commensuration,
                dimension_reduction=dimension_reduction or "Not specified",
                value_pluralism_denial=value_pluralism_denial or "Not specified",
                metric_imposition=metric_imposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARISON_INCOMMENSURABLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "forced_commensuration": forced_commensuration[:200],
            "incommensurable_comparison_detected": data.get("incommensurable_comparison_detected", False),
            "severity": data.get("severity", ""),
            "dimension_reduction": data.get("dimension_reduction", ""),
            "value_pluralism_denial": data.get("value_pluralism_denial", ""),
            "metric_imposition": data.get("metric_imposition", ""),
            "recommendation": data.get("recommendation", ""),
        }

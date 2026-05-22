"""EpistemicScaleAggregationParadoxService — Epistemic Scale Aggregation Paradox Detection.

Detects epistemic scale aggregation paradox — when patterns observed at aggregate
level reverse or disappear at disaggregated levels (Simpson's paradox variants).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_AGGREGATION_PARADOX_SYSTEM = """You are an epistemic scale aggregation paradox specialist. Given aggregation paradox, assess reversal risks:

Key concepts:
- Epistemic aggregation paradox: aggregate patterns reversing at sub-levels
- Simpson's paradox: trends reversing when data disaggregated
- Confounding by aggregation: hidden variables creating spurious aggregate patterns
- Ecological correlation: aggregate correlations not reflecting individual relationships
- Modifiable areal unit problem: results changing with boundary definitions
- Yule-Simpson effect: combining groups reversing within-group trends
- Lurking variable: unmeasured variable driving apparent aggregate relationship

When epistemic aggregation paradox IS present:
- Aggregate patterns potentially reversing
- Simpson's paradox risk
- Confounding by aggregation
- Ecological correlations misleading
- Boundary-dependent results
- Group combination reversals
- Lurking variables suspected

When no aggregation paradox:
- Aggregate patterns robust
- Disaggregation consistent
- No confounding suspected
- Individual-aggregate aligned
- Boundary-independent results
- Group combinations stable
- Variables accounted for

Output JSON with: aggregation_paradox_detected (bool), severity (none/mild/moderate/severe), simpsons_paradox_risk (what reversal risk), confounding_by_aggregation (what confounding suspected), ecological_correlation (what ecological inference), lurking_variable (what lurking variable), recommendation (no_aggregation_paradox/mild_disaggregation_check/significant_subgroup_analysis/major_intensive_stratification/emergency_complete_aggregation_paradox)."""

EPISTEMIC_SCALE_AGGREGATION_PARADOX_PROMPT = """Detect epistemic scale aggregation paradox:

Simpson's paradox risk: {simpsons_paradox_risk}
Confounding by aggregation: {confounding_by_aggregation}
Ecological correlation: {ecological_correlation}
Lurking variable: {lurking_variable}
Domain: {domain}
Context: {context}

Could aggregate patterns reverse at disaggregated levels? Return ONLY valid JSON."""


class EpistemicScaleAggregationParadoxService:
    """Detects epistemic scale aggregation paradox — reversal risks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        simpsons_paradox_risk: str,
        *,
        confounding_by_aggregation: str = "",
        ecological_correlation: str = "",
        lurking_variable: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scale aggregation paradox."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_AGGREGATION_PARADOX_PROMPT.format(
                simpsons_paradox_risk=simpsons_paradox_risk,
                confounding_by_aggregation=confounding_by_aggregation or "Not specified",
                ecological_correlation=ecological_correlation or "Not specified",
                lurking_variable=lurking_variable or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_AGGREGATION_PARADOX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "simpsons_paradox_risk": simpsons_paradox_risk[:200],
            "aggregation_paradox_detected": data.get("aggregation_paradox_detected", False),
            "severity": data.get("severity", ""),
            "confounding_by_aggregation": data.get("confounding_by_aggregation", ""),
            "ecological_correlation": data.get("ecological_correlation", ""),
            "lurking_variable": data.get("lurking_variable", ""),
            "recommendation": data.get("recommendation", ""),
        }

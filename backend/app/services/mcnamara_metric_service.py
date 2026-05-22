"""McNamaraMetricService — McNamara Metric Detection.

Detects McNamara metric fallacy — making decisions based solely
on quantitative metrics while ignoring qualitative factors that
may be more important but harder to measure. Named after Robert
McNamara's reliance on body counts in Vietnam.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MCNAMARA_METRIC_SYSTEM = """You are a McNamara metric specialist. Given a decision or assessment, evaluate whether it over-relies on quantitative metrics while ignoring important qualitative factors:

Key concepts:
- McNamara fallacy: measuring what's easy, ignoring what matters
- Quantitative bias: preferring numbers over judgment
- Metric fixation: obsession with measurable indicators
- Goodhart's law: when a measure becomes a target, it ceases to be good
- Surrogate endpoints: measuring proxies instead of outcomes
- Dashboard blindness: trusting dashboards over ground truth
- Qualitative evidence: important information that resists quantification

When McNamara metric IS present:
- Decisions based solely on KPIs while ignoring user experience
- "The numbers look good" when qualitative feedback is negative
- Measuring activity instead of outcomes
- Ignoring hard-to-measure factors (morale, trust, quality)
- Optimizing metrics that don't capture what actually matters
- "If you can't measure it, it doesn't exist"
- Body count mentality: measuring the wrong thing precisely

When McNamara metric is NOT present:
- Quantitative metrics used alongside qualitative assessment
- Metrics are validated against actual outcomes
- Hard-to-measure factors are acknowledged and assessed
- The limitations of metrics are discussed
- Multiple metrics capture different dimensions
- Qualitative feedback is weighted appropriately
- Metrics serve as indicators, not as the full picture

Output JSON with: mcnamara_metric_present (bool), severity (none/mild/moderate/severe), metrics_used (what is being measured), qualitative_ignored (what important factors are unmeasured), proxy_validity (do metrics actually capture what matters), decision_quality (how does metric-only thinking affect decisions), recommendation (no_mcnamara_metric/mild_metric_bias/significant_mcnamara_metric/major_measurement_fixation/include_qualitative_factors)."""

MCNAMARA_METRIC_PROMPT = """Detect McNamara metric fallacy:

Decision: {decision}
Metrics used: {metrics}
Qualitative factors: {qualitative}
Outcome alignment: {alignment}
Domain: {domain}
Context: {context}

Does this over-rely on quantitative metrics while ignoring important qualitative factors? Return ONLY valid JSON."""


class McNamaraMetricService:
    """Detects McNamara metric — measuring what's easy, ignoring what matters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        metrics: str = "",
        qualitative: str = "",
        alignment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect McNamara metric fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MCNAMARA_METRIC_PROMPT.format(
                decision=decision,
                metrics=metrics or "Not specified",
                qualitative=qualitative or "Not specified",
                alignment=alignment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MCNAMARA_METRIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "mcnamara_metric_present": data.get("mcnamara_metric_present", False),
            "severity": data.get("severity", ""),
            "metrics_used": data.get("metrics_used", ""),
            "qualitative_ignored": data.get("qualitative_ignored", ""),
            "proxy_validity": data.get("proxy_validity", ""),
            "recommendation": data.get("recommendation", ""),
        }

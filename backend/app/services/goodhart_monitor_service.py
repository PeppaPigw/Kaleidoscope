"""GoodhartMonitorService — Active Goodhart's Law Degradation Detection.

Monitors whether optimization pressure is actively degrading a metric.
Unlike proxy_validity_assess (which checks if a proxy is valid),
this detects when a previously-valid metric is being corrupted by
the act of optimizing for it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOODHART_SYSTEM = """You are a Goodhart's Law monitor. Given a metric being optimized, assess whether optimization pressure is degrading it:
- Is the metric still measuring what it originally measured?
- Are people gaming the metric without improving the underlying thing?
- Has the metric become a target (and thus ceased to be a good measure)?
- What behaviors has optimization pressure created?
- Is there a divergence between metric improvement and real improvement?

Output JSON with: degradation_detected (bool), degradation_stage (healthy/early_warning/active_degradation/fully_gamed/metric_dead), metric_target_divergence (0-1, how much metric has diverged from what it should measure), gaming_behaviors (list of: behavior, who_does_it, metric_impact, real_impact), optimization_pressure_source (who is pushing to improve this metric), original_validity (how well the metric worked before optimization pressure), current_validity (how well it works now), degradation_timeline (how quickly it's degrading), leading_indicators (early signs that degradation is happening), metric_autopsy (if fully gamed, what killed it), replacement_candidates (list of harder-to-game alternatives), recommendation (metric_healthy/add_guardrails/supplement_with_other_metrics/replace_metric/stop_optimizing)."""

GOODHART_PROMPT = """Monitor Goodhart's Law degradation:

Metric: {metric}
What it should measure: {intended_measure}
Who optimizes it: {optimizers}
Optimization pressure: {pressure}
Domain: {domain}
Context: {context}

Is optimization degrading this metric? Return ONLY valid JSON."""


class GoodhartMonitorService:
    """Monitors active Goodhart's Law degradation of metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def monitor(
        self,
        metric: str,
        *,
        intended_measure: str = "",
        optimizers: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Monitor Goodhart's Law degradation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOODHART_PROMPT.format(
                metric=metric,
                intended_measure=intended_measure or "Not specified",
                optimizers=optimizers or "Not specified",
                pressure=pressure or "High",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GOODHART_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metric": metric[:200],
            "degradation_detected": data.get("degradation_detected", False),
            "degradation_stage": data.get("degradation_stage", ""),
            "metric_target_divergence": data.get("metric_target_divergence", 0),
            "gaming_behaviors": data.get("gaming_behaviors", []),
            "optimization_pressure_source": data.get("optimization_pressure_source", ""),
            "original_validity": data.get("original_validity", ""),
            "current_validity": data.get("current_validity", ""),
            "degradation_timeline": data.get("degradation_timeline", ""),
            "leading_indicators": data.get("leading_indicators", []),
            "metric_autopsy": data.get("metric_autopsy", ""),
            "replacement_candidates": data.get("replacement_candidates", []),
            "recommendation": data.get("recommendation", ""),
        }

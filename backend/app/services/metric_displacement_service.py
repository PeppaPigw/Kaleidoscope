"""MetricDisplacementService — Metric Displacement Detection.

Detects metric displacement — metrics displacing the goals they were
meant to measure, where optimizing for the metric diverges from
achieving the actual objective (Goodhart's Law in practice).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

METRIC_DISPLACEMENT_SYSTEM = """You are a metric displacement specialist. Given a measurement system, assess whether metrics have displaced their intended goals:

Key concepts:
- Metric displacement: metric replaces the goal it measures
- Goodhart's Law: measure becomes target, ceases to be good measure
- Goal displacement: original goal forgotten, metric becomes goal
- Gaming metrics: optimizing metric without achieving goal
- Measurement fixation: focus on measurable at expense of important
- Proxy confusion: proxy treated as the thing itself
- Campbell's Law: measurement corrupts what it measures

When metric displacement IS present:
- Metric has become the goal rather than measuring it
- Optimizing metric diverges from achieving objective
- Original goal forgotten in favor of metric
- Metric being gamed without achieving purpose
- Measurable prioritized over important
- Proxy confused with what it represents
- Measurement corrupting the process it measures

When metrics are appropriate:
- Metrics serve as indicators, not goals
- Original objectives remain primary
- Metric limitations acknowledged
- Gaming detected and addressed
- Important unmeasured factors considered
- Proxy nature of metrics recognized
- Measurement improves rather than corrupts

Output JSON with: displacement_present (bool), severity (none/mild/moderate/severe), system (what system is analyzed), metric (what metric has displaced), original_goal (what goal was intended), divergence (how metric and goal diverge), recommendation (appropriate_measurement/mild_metric_focus/significant_metric_displacement/major_goal_displacement/reconnect_metrics_to_goals)."""

METRIC_DISPLACEMENT_PROMPT = """Detect metric displacement:

System: {system}
Metric used: {metric}
Original goal: {goal}
Current behavior: {behavior}
Domain: {domain}
Context: {context}

Have metrics displaced the goals they were meant to measure? Return ONLY valid JSON."""


class MetricDisplacementService:
    """Detects metric displacement — metrics displacing their intended goals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        metric: str = "",
        goal: str = "",
        behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect metric displacement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METRIC_DISPLACEMENT_PROMPT.format(
                system=system,
                metric=metric or "Not specified",
                goal=goal or "Not specified",
                behavior=behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=METRIC_DISPLACEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "displacement_present": data.get("displacement_present", False),
            "severity": data.get("severity", ""),
            "metric": data.get("metric", ""),
            "original_goal": data.get("original_goal", ""),
            "divergence": data.get("divergence", ""),
            "recommendation": data.get("recommendation", ""),
        }

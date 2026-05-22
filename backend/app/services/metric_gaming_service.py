"""MetricGamingService — Metric Gaming Detection.

Detects metric gaming — when people optimize for metrics rather
than the underlying goals the metrics were meant to track,
producing good numbers without good outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

METRIC_GAMING_SYSTEM = """You are a metric gaming specialist. Given a performance situation, assess whether metrics are being gamed rather than genuinely improved:

Key concepts:
- Gaming: optimizing metric without improving underlying reality
- Teaching to the test: preparing for measurement rather than learning
- Cream skimming: selecting easy cases to improve metrics
- Threshold effects: effort concentrated at metric boundaries
- Metric manipulation: changing how things are counted
- Displacement: improving one metric by worsening unmeasured things
- Strategic behavior: rational responses to incentives that undermine goals

When metric gaming IS present:
- Metric improving without underlying reality improving
- Behavior optimized for measurement rather than outcomes
- Easy cases selected to boost numbers
- Effort concentrated at metric thresholds
- Counting methods changed to improve appearance
- Unmeasured dimensions degrading as measured ones improve
- Strategic behavior undermining metric's purpose

When improvement is genuine:
- Metric improvement reflects real underlying improvement
- Behavior focused on outcomes, not just measurement
- All cases treated appropriately regardless of metric impact
- Effort distributed based on need, not metric impact
- Counting methods consistent and transparent
- Multiple dimensions improving together
- Behavior aligned with goals, not just incentives

Output JSON with: gaming_present (bool), severity (none/mild/moderate/severe), metric (what metric is gamed), behavior (what gaming behavior is observed), underlying_reality (what the actual situation is), displacement (what is worsened to improve metric), recommendation (genuine_improvement/mild_gaming/significant_metric_manipulation/major_gaming_culture/redesign_metrics)."""

METRIC_GAMING_PROMPT = """Detect metric gaming:

Situation: {situation}
Metric: {metric}
Behavior: {behavior}
Outcomes: {outcomes}
Domain: {domain}
Context: {context}

Are metrics being gamed rather than genuinely improved? Return ONLY valid JSON."""


class MetricGamingService:
    """Detects metric gaming — optimizing metrics without improving reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        metric: str = "",
        behavior: str = "",
        outcomes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect metric gaming."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METRIC_GAMING_PROMPT.format(
                situation=situation,
                metric=metric or "Not specified",
                behavior=behavior or "Not specified",
                outcomes=outcomes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=METRIC_GAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "gaming_present": data.get("gaming_present", False),
            "severity": data.get("severity", ""),
            "metric": data.get("metric", ""),
            "behavior": data.get("behavior", ""),
            "displacement": data.get("displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }

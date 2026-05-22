"""GoodhartLawService — Goodhart's Law Detection.

Detects Goodhart's Law violations — when a measure becomes a
target, it ceases to be a good measure because people optimize
for the metric rather than the underlying goal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOODHART_LAW_SYSTEM = """You are a Goodhart's Law specialist. Given a metric or target, assess whether it has become corrupted by being targeted:

Key concepts:
- Goodhart's Law: when a measure becomes a target, it ceases to be a good measure
- Campbell's Law: the more a metric is used for decisions, the more it gets corrupted
- Gaming: optimizing the metric without improving the underlying reality
- Cobra effect: incentives producing opposite of intended outcome
- Teaching to the test: optimizing for measurement rather than learning
- Metric fixation: over-reliance on quantitative indicators
- Surrogate endpoint: measuring proxy when real outcome is what matters

When Goodhart's Law IS operating:
- Metric being optimized directly rather than underlying goal
- Gaming or manipulation of the metric observed
- Metric no longer correlates with original purpose
- Perverse incentives created by targeting the metric
- People optimizing for measurement rather than reality
- Metric divorced from the thing it was meant to measure
- Unintended consequences of metric-targeting

When metrics are healthy:
- Metric still correlates with underlying goal
- Multiple metrics used to prevent gaming
- Metric regularly validated against reality
- Gaming detected and corrected
- Metric used as indicator, not sole target
- Underlying goal remains primary focus
- Metric updated when correlation breaks down

Output JSON with: goodhart_present (bool), severity (none/mild/moderate/severe), metric (what metric is targeted), original_purpose (what it was meant to measure), gaming (how it is being gamed), divergence (how metric diverged from purpose), recommendation (metric_healthy/mild_gaming/significant_divergence/major_goodhart_corruption/redesign_incentives)."""

GOODHART_LAW_PROMPT = """Detect Goodhart's Law:

Metric: {metric}
Target: {target}
Behavior observed: {behavior}
Original purpose: {purpose}
Domain: {domain}
Context: {context}

Has this metric been corrupted by being used as a target? Return ONLY valid JSON."""


class GoodhartLawService:
    """Detects Goodhart's Law — metrics corrupted by being targeted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metric: str,
        *,
        target: str = "",
        behavior: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Goodhart's Law."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOODHART_LAW_PROMPT.format(
                metric=metric,
                target=target or "Not specified",
                behavior=behavior or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GOODHART_LAW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metric": metric[:200],
            "goodhart_present": data.get("goodhart_present", False),
            "severity": data.get("severity", ""),
            "original_purpose": data.get("original_purpose", ""),
            "gaming": data.get("gaming", ""),
            "divergence": data.get("divergence", ""),
            "recommendation": data.get("recommendation", ""),
        }

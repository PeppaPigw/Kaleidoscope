"""CampbellLawService — Campbell's Law Detection.

Detects Campbell's Law — the more any quantitative social
indicator is used for social decision-making, the more subject
it will be to corruption pressures and the more apt it will be
to distort and corrupt the social processes it is intended to
monitor. Donald Campbell (1979). Related to Goodhart's Law but
emphasizes corruption and gaming rather than just metric drift.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CAMPBELL_SYSTEM = """You are a Campbell's Law specialist. Given a metric being used for decisions, assess whether Campbell's Law corruption is occurring:

Key concepts (Campbell, 1979):
- Campbell's Law: metrics used for decisions get corrupted
- Gaming: optimizing the metric without improving the underlying reality
- Teaching to the test: improving scores without improving learning
- Metric corruption: the indicator no longer measures what it was designed to measure
- Perverse incentives: the metric creates incentives contrary to its purpose
- Goodhart overlap: "when a measure becomes a target, it ceases to be a good measure"
- McNamara overlap: relying on corrupted metrics while ignoring qualitative reality

Examples:
- Schools: teaching to standardized tests, not teaching understanding
- Hospitals: refusing difficult patients to improve mortality statistics
- Police: downgrading crimes to improve crime statistics
- Wells Fargo: opening fake accounts to meet account-opening targets
- Research: p-hacking to meet publication thresholds

When Campbell's Law IS operating:
- The metric is improving but the underlying reality isn't
- People are gaming the measurement rather than improving performance
- The metric has become a target with high-stakes consequences
- Behavior has shifted to optimize the metric specifically
- The metric no longer correlates with what it was designed to measure

When metric-driven improvement IS genuine:
- Improvements in the metric correspond to real improvements
- Multiple independent metrics all improve together
- Qualitative assessment confirms quantitative improvement
- No evidence of gaming or manipulation
- The metric is one input among many, not the sole decision criterion

Output JSON with: campbell_law_present (bool), severity (none/mild/moderate/severe), metric (what metric is being used), decision_context (what decisions it drives), gaming_behavior (how the metric is being gamed), corruption_mechanism (how the metric is being corrupted), metric_reality_gap (how far the metric has diverged from reality), perverse_incentives (what bad behavior the metric encourages), who_games (who is gaming the metric), stakes (what consequences attach to the metric), qualitative_check (does qualitative assessment match the metric?), multiple_metrics (bool — are other metrics used as cross-checks?), original_purpose (what the metric was designed to measure), current_meaning (what the metric actually measures now), recommendation (metric_valid/mild_gaming/significant_corruption/severe_campbell_law/replace_metric_system)."""

CAMPBELL_PROMPT = """Detect Campbell's Law:

Metric/Indicator: {metric}
How used: {usage}
Observed behavior: {behavior}
Outcomes: {outcomes}
Domain: {domain}
Context: {context}

Is Campbell's Law corrupting this metric? Return ONLY valid JSON."""


class CampbellLawService:
    """Detects Campbell's Law — metrics used for decisions getting corrupted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metric: str,
        *,
        usage: str = "",
        behavior: str = "",
        outcomes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Campbell's Law."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CAMPBELL_PROMPT.format(
                metric=metric,
                usage=usage or "Not specified",
                behavior=behavior or "Not specified",
                outcomes=outcomes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CAMPBELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metric": metric[:200],
            "campbell_law_present": data.get("campbell_law_present", False),
            "severity": data.get("severity", ""),
            "decision_context": data.get("decision_context", ""),
            "gaming_behavior": data.get("gaming_behavior", ""),
            "corruption_mechanism": data.get("corruption_mechanism", ""),
            "metric_reality_gap": data.get("metric_reality_gap", ""),
            "perverse_incentives": data.get("perverse_incentives", ""),
            "who_games": data.get("who_games", ""),
            "stakes": data.get("stakes", ""),
            "qualitative_check": data.get("qualitative_check", ""),
            "multiple_metrics": data.get("multiple_metrics", False),
            "original_purpose": data.get("original_purpose", ""),
            "current_meaning": data.get("current_meaning", ""),
            "recommendation": data.get("recommendation", ""),
        }

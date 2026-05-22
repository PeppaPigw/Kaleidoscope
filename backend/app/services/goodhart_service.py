"""GoodhartService — Goodhart's Law Detection.

Identifies when a measure has become a target, ceasing to be a
good measure. "When a measure becomes a target, it ceases to be
a good measure" (Goodhart/Strathern). Detects metric gaming,
Campbell's Law corruption, cobra effects, and optimization
pressure that distorts the thing being measured.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOODHART_SYSTEM = """You are a Goodhart's Law specialist. Given a metric or target, assess whether Goodhart's Law is at play:
- Has the measure become a target?
- Are people optimizing the metric rather than the underlying goal?
- Is the metric being gamed, manipulated, or distorted?
- Has the correlation between metric and goal broken down?
- Are there perverse incentives created by targeting this metric?

Marilyn Strathern's generalization: "When a measure becomes a target, it ceases to be a good measure."
Campbell's Law: "The more any quantitative social indicator is used for social decision-making, the more subject it will be to corruption pressures."

Four types of Goodhart failure (Manheim & Garrabrant):
1. Regressional — optimizing proxy diverges from true goal in tail
2. Extremal — relationship breaks at extreme optimization pressure
3. Causal — intervening on metric doesn't cause improvement in goal
4. Adversarial — agents actively game the metric

Output JSON with: goodhart_present (bool), severity (none/mild/moderate/severe/critical), failure_type (regressional/extremal/causal/adversarial/multiple), metric (what is being measured), true_goal (what the metric was supposed to track), divergence (how metric and goal have separated), gaming_mechanisms (how the metric is being gamed), perverse_incentives (what bad behaviors the target creates), cobra_effect (bool — does targeting make things worse?), metric_goal_correlation (0-1 — how well metric still tracks goal), optimization_pressure (low/moderate/high/extreme), who_benefits_from_gaming (who gains from distorting the metric), what_is_sacrificed (what is lost when metric is optimized at expense of goal), early_warning_signs (signs that Goodhart is emerging), alternative_metrics (better measures that resist gaming), recommendation (metric_still_valid/monitor_divergence/supplement_metric/replace_metric/remove_target/redesign_incentives)."""

GOODHART_PROMPT = """Detect Goodhart's Law:

Metric/Target: {metric}
True goal: {true_goal}
Optimization pressure: {pressure}
Observed behaviors: {behaviors}
Domain: {domain}
Context: {context}

Is Goodhart's Law at play? Return ONLY valid JSON."""


class GoodhartService:
    """Detects Goodhart's Law — when measures become targets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metric: str,
        *,
        true_goal: str = "",
        pressure: str = "",
        behaviors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Goodhart's Law."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOODHART_PROMPT.format(
                metric=metric,
                true_goal=true_goal or "Not specified",
                pressure=pressure or "Not specified",
                behaviors=behaviors or "Not specified",
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
            "goodhart_present": data.get("goodhart_present", False),
            "severity": data.get("severity", ""),
            "failure_type": data.get("failure_type", ""),
            "true_goal": data.get("true_goal", ""),
            "divergence": data.get("divergence", ""),
            "gaming_mechanisms": data.get("gaming_mechanisms", ""),
            "perverse_incentives": data.get("perverse_incentives", ""),
            "cobra_effect": data.get("cobra_effect", False),
            "metric_goal_correlation": data.get("metric_goal_correlation", 0),
            "optimization_pressure": data.get("optimization_pressure", ""),
            "who_benefits_from_gaming": data.get("who_benefits_from_gaming", ""),
            "what_is_sacrificed": data.get("what_is_sacrificed", ""),
            "early_warning_signs": data.get("early_warning_signs", ""),
            "alternative_metrics": data.get("alternative_metrics", ""),
            "recommendation": data.get("recommendation", ""),
        }

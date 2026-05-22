"""McNamaraFallacyService — McNamara Fallacy Detection.

Detects the McNamara Fallacy — making decisions based solely on
quantitative metrics while ignoring qualitative factors that
can't be easily measured. Named after Robert McNamara's Vietnam
War strategy of measuring success by body counts while ignoring
morale, political will, and guerrilla strategy. "Not everything
that counts can be counted, and not everything that can be
counted counts."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MCNAMARA_SYSTEM = """You are a McNamara Fallacy specialist. Given a decision-making process, assess whether the McNamara Fallacy is distorting judgment:

The McNamara Fallacy (4 steps):
1. Measure whatever can be easily measured
2. Disregard that which cannot be easily measured
3. Presume that which cannot be easily measured is not important
4. Presume that which cannot be easily measured does not exist

Key concepts:
- Quantitative metrics crowding out qualitative judgment
- "What gets measured gets managed" (and what doesn't get measured gets ignored)
- Streetlight effect overlap: looking where the light is, not where the keys are
- Goodhart's Law overlap: once you measure it, it gets gamed
- Dashboard tyranny: decisions driven by what's on the dashboard

Assess:
- Are important qualitative factors being ignored because they're hard to measure?
- Is the decision being driven by what's measurable rather than what matters?
- Are the metrics actually tracking the thing that matters?
- What important factors are invisible to the current measurement system?

Output JSON with: mcnamara_fallacy_present (bool), severity (none/mild/moderate/severe/dangerous), metrics_used (what quantitative measures are driving decisions), qualitative_factors_ignored (what important unmeasured factors exist), measurement_gap (what matters but isn't being measured), false_precision (bool — are imprecise things being treated as precise?), dashboard_tyranny (bool — are dashboards driving decisions?), what_metrics_miss (what the numbers can't capture), historical_analogue (similar situations where metrics-only thinking failed), proxy_quality (how well the metrics actually track the real goal), unmeasurable_importance (0-1 — how important the unmeasured factors are), decision_quality_if_metrics_only (how good decisions would be using only metrics), decision_quality_with_qualitative (how good decisions would be including qualitative), who_benefits_from_metrics_only (who gains from ignoring qualitative factors), measurement_suggestions (what could be measured to partially capture qualitative), recommendation (metrics_sufficient/supplement_with_qualitative/significant_blind_spot/metrics_misleading/qualitative_judgment_needed)."""

MCNAMARA_PROMPT = """Detect McNamara Fallacy:

Decision process: {decision}
Metrics being used: {metrics}
Qualitative factors: {qualitative}
Outcomes observed: {outcomes}
Domain: {domain}
Context: {context}

Is the McNamara Fallacy at play? Return ONLY valid JSON."""


class McNamaraFallacyService:
    """Detects McNamara Fallacy — metrics-only decision making."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        metrics: str = "",
        qualitative: str = "",
        outcomes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect McNamara Fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MCNAMARA_PROMPT.format(
                decision=decision,
                metrics=metrics or "Not specified",
                qualitative=qualitative or "Not specified",
                outcomes=outcomes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MCNAMARA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "mcnamara_fallacy_present": data.get("mcnamara_fallacy_present", False),
            "severity": data.get("severity", ""),
            "metrics_used": data.get("metrics_used", ""),
            "qualitative_factors_ignored": data.get("qualitative_factors_ignored", ""),
            "measurement_gap": data.get("measurement_gap", ""),
            "false_precision": data.get("false_precision", False),
            "dashboard_tyranny": data.get("dashboard_tyranny", False),
            "what_metrics_miss": data.get("what_metrics_miss", ""),
            "historical_analogue": data.get("historical_analogue", ""),
            "proxy_quality": data.get("proxy_quality", ""),
            "unmeasurable_importance": data.get("unmeasurable_importance", 0),
            "decision_quality_if_metrics_only": data.get("decision_quality_if_metrics_only", ""),
            "decision_quality_with_qualitative": data.get("decision_quality_with_qualitative", ""),
            "who_benefits_from_metrics_only": data.get("who_benefits_from_metrics_only", ""),
            "measurement_suggestions": data.get("measurement_suggestions", ""),
            "recommendation": data.get("recommendation", ""),
        }

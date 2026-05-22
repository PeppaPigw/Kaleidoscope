"""EpistemicGrowthChartService — Epistemic Growth Chart Detection.

Detects epistemic growth chart anomalies — intellectual systems growing
outside expected percentile ranges.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROWTH_CHART_SYSTEM = """You are an epistemic growth chart specialist. Given intellectual growth patterns, assess anomalies:

Key concepts:
- Epistemic growth chart: tracking intellectual development over time
- Percentile crossing: moving between growth curves
- Failure to thrive: falling off growth curve
- Macrocephaly: intellectual head growing too fast
- Microcephaly: intellectual head growing too slow
- Growth velocity: rate of intellectual development
- Constitutional delay: normal variant of slow growth

When epistemic growth chart anomalies ARE present:
- Growing outside expected ranges
- Crossing percentile curves
- Falling off growth curve
- Head growing too fast
- Head growing too slow
- Abnormal development rate
- Delay beyond normal variation

When no growth anomalies:
- Within expected ranges
- Following percentile curve
- Maintaining growth trajectory
- Normal head growth
- Appropriate development rate
- Normal variation
- On expected curve

Output JSON with: growth_anomaly (bool), severity (none/mild/moderate/severe), percentile_status (what curve position), crossing_direction (what trajectory change), velocity_status (what rate), head_growth (what intellectual size), recommendation (no_anomaly/mild_monitoring/significant_investigation/major_intervention/emergency_acute_growth_failure)."""

EPISTEMIC_GROWTH_CHART_PROMPT = """Detect epistemic growth chart anomaly:

Percentile status: {percentile_status}
Crossing direction: {crossing_direction}
Velocity status: {velocity_status}
Head growth: {head_growth}
Domain: {domain}
Context: {context}

Is the intellectual system growing outside expected percentile ranges? Return ONLY valid JSON."""


class EpistemicGrowthChartService:
    """Detects epistemic growth chart anomalies — growing outside expected ranges."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        percentile_status: str,
        *,
        crossing_direction: str = "",
        velocity_status: str = "",
        head_growth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic growth chart anomaly."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROWTH_CHART_PROMPT.format(
                percentile_status=percentile_status,
                crossing_direction=crossing_direction or "Not specified",
                velocity_status=velocity_status or "Not specified",
                head_growth=head_growth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROWTH_CHART_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "percentile_status": percentile_status[:200],
            "growth_anomaly": data.get("growth_anomaly", False),
            "severity": data.get("severity", ""),
            "crossing_direction": data.get("crossing_direction", ""),
            "velocity_status": data.get("velocity_status", ""),
            "head_growth": data.get("head_growth", ""),
            "recommendation": data.get("recommendation", ""),
        }

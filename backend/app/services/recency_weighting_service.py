"""RecencyWeightingService — Recency Weighting Detection.

Detects recency weighting bias — the tendency to overweight
recent events when making predictions or assessments, while
underweighting older but potentially more representative data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RECENCY_WEIGHTING_SYSTEM = """You are a recency weighting specialist. Given a prediction or assessment, determine whether recent events are being overweighted:

Key concepts:
- Recency bias: overweighting recent observations
- Availability heuristic: recent events are more mentally available
- Base rate neglect: recent events overriding long-term patterns
- Mean reversion: recent extremes likely to revert
- Sample size: recent data is a small sample of the full distribution
- Regime change: when recent data IS more relevant (legitimate)
- Exponential discounting: how quickly old data loses relevance

When recency weighting IS problematic:
- Recent events dominating predictions despite small sample
- Long-term base rates ignored in favor of recent trends
- One recent event changing entire assessment
- "Things are different now" without structural justification
- Recent performance extrapolated as new normal
- Panic or euphoria based on recent events
- Historical patterns dismissed because of recent exceptions

When recency weighting is NOT problematic:
- Recent data weighted appropriately given sample size
- Long-term base rates incorporated alongside recent data
- Structural changes justify increased weight on recent data
- Recent events contextualized within historical distribution
- Both recent and historical data inform the assessment
- Regime changes identified with evidence, not assumption
- Appropriate decay function applied to older data

Output JSON with: overweighting_present (bool), severity (none/mild/moderate/severe), recent_events (what recent data is being emphasized), historical_base (what long-term data exists), weight_ratio (how much more recent data is weighted), regime_change (is there a legitimate structural change), recommendation (appropriate_weighting/mild_recency_bias/significant_overweighting/major_recency_distortion/incorporate_base_rates)."""

RECENCY_WEIGHTING_PROMPT = """Detect recency weighting bias:

Assessment: {assessment}
Recent events: {recent}
Historical data: {historical}
Time horizon: {horizon}
Domain: {domain}
Context: {context}

Are recent events being overweighted relative to historical patterns? Return ONLY valid JSON."""


class RecencyWeightingService:
    """Detects recency weighting — overweighting recent events in predictions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        recent: str = "",
        historical: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect recency weighting bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RECENCY_WEIGHTING_PROMPT.format(
                assessment=assessment,
                recent=recent or "Not specified",
                historical=historical or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RECENCY_WEIGHTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "overweighting_present": data.get("overweighting_present", False),
            "severity": data.get("severity", ""),
            "recent_events": data.get("recent_events", ""),
            "historical_base": data.get("historical_base", ""),
            "regime_change": data.get("regime_change", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicTemporalRecencyBiasService — Epistemic Temporal Recency Bias Detection.

Detects epistemic temporal recency bias — overweighting recent events and data
while underweighting historical patterns and long-term trends.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_RECENCY_BIAS_SYSTEM = """You are an epistemic temporal recency bias specialist. Given recency bias, assess temporal weighting distortion:

Key concepts:
- Epistemic recency bias: overweighting recent events over historical patterns
- Availability cascade: recent events more cognitively available
- Trend extrapolation: projecting recent trends indefinitely
- Base rate neglect: ignoring long-term frequencies for recent observations
- Regime change illusion: assuming recent changes are permanent shifts
- Historical amnesia: forgetting similar past episodes
- Novelty illusion: treating recurring patterns as unprecedented

When epistemic recency bias IS present:
- Recent events overweighted
- Historical patterns ignored
- Recent trends extrapolated
- Base rates neglected
- Changes assumed permanent
- Past episodes forgotten
- Patterns treated as novel

When no recency bias:
- Temporal weighting appropriate
- Historical patterns considered
- Trends contextualized
- Base rates incorporated
- Change durability assessed
- Past episodes referenced
- Recurrence recognized

Output JSON with: recency_bias_detected (bool), severity (none/mild/moderate/severe), availability_cascade (what recent events overweighted), trend_extrapolation (what trends extrapolated), historical_amnesia (what history forgotten), novelty_illusion (what treated as novel), recommendation (no_recency_bias/mild_historical_checking/significant_temporal_rebalancing/major_intensive_historical_analysis/emergency_complete_recency_bias)."""

EPISTEMIC_TEMPORAL_RECENCY_BIAS_PROMPT = """Detect epistemic temporal recency bias:

Availability cascade: {availability_cascade}
Trend extrapolation: {trend_extrapolation}
Historical amnesia: {historical_amnesia}
Novelty illusion: {novelty_illusion}
Domain: {domain}
Context: {context}

Are recent events being overweighted relative to historical patterns? Return ONLY valid JSON."""


class EpistemicTemporalRecencyBiasService:
    """Detects epistemic temporal recency bias — recent overweighting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        availability_cascade: str,
        *,
        trend_extrapolation: str = "",
        historical_amnesia: str = "",
        novelty_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal recency bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_RECENCY_BIAS_PROMPT.format(
                availability_cascade=availability_cascade,
                trend_extrapolation=trend_extrapolation or "Not specified",
                historical_amnesia=historical_amnesia or "Not specified",
                novelty_illusion=novelty_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_RECENCY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "availability_cascade": availability_cascade[:200],
            "recency_bias_detected": data.get("recency_bias_detected", False),
            "severity": data.get("severity", ""),
            "trend_extrapolation": data.get("trend_extrapolation", ""),
            "historical_amnesia": data.get("historical_amnesia", ""),
            "novelty_illusion": data.get("novelty_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

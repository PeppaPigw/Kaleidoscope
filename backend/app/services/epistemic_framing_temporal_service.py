"""EpistemicFramingTemporalService — Epistemic Temporal Framing Detection.

Detects epistemic framing temporal manipulation — choosing temporal windows
that change interpretation of data or events.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAMING_TEMPORAL_SYSTEM = """You are an epistemic framing temporal specialist. Given temporal framing, assess time window manipulation:

Key concepts:
- Epistemic temporal framing: choosing time windows to change interpretation
- Cherry-picked start dates: choosing start dates that favor narrative
- Truncated time series: cutting time series to hide inconvenient trends
- Peak/trough selection: starting from peaks or troughs to exaggerate change
- Recency bias framing: emphasizing recent data to override long-term patterns
- Historical cherry-picking: selecting historical periods for comparison
- Trend line manipulation: choosing periods that create desired trend

When epistemic temporal framing IS present:
- Time windows strategically chosen
- Start dates cherry-picked
- Time series truncated
- Peaks/troughs selected
- Recency bias exploited
- Historical periods cherry-picked
- Trend lines manipulated

When no temporal framing:
- Time windows justified
- Start dates appropriate
- Full time series shown
- Representative periods chosen
- Recency balanced with history
- Historical comparisons fair
- Trends honestly represented

Output JSON with: temporal_framing_detected (bool), severity (none/mild/moderate/severe), cherry_picked_dates (what dates cherry-picked), truncated_series (what series truncated), peak_trough_selection (what peaks/troughs selected), trend_manipulation (what trends manipulated), recommendation (no_temporal_framing/mild_window_justification/significant_full_series_inclusion/major_intensive_temporal_audit/emergency_complete_temporal_manipulation)."""

EPISTEMIC_FRAMING_TEMPORAL_PROMPT = """Detect epistemic temporal framing manipulation:

Cherry picked dates: {cherry_picked_dates}
Truncated series: {truncated_series}
Peak trough selection: {peak_trough_selection}
Trend manipulation: {trend_manipulation}
Domain: {domain}
Context: {context}

Are temporal windows being chosen to change interpretation? Return ONLY valid JSON."""


class EpistemicFramingTemporalService:
    """Detects epistemic temporal framing — time window manipulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cherry_picked_dates: str,
        *,
        truncated_series: str = "",
        peak_trough_selection: str = "",
        trend_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal framing manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAMING_TEMPORAL_PROMPT.format(
                cherry_picked_dates=cherry_picked_dates,
                truncated_series=truncated_series or "Not specified",
                peak_trough_selection=peak_trough_selection or "Not specified",
                trend_manipulation=trend_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAMING_TEMPORAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cherry_picked_dates": cherry_picked_dates[:200],
            "temporal_framing_detected": data.get("temporal_framing_detected", False),
            "severity": data.get("severity", ""),
            "truncated_series": data.get("truncated_series", ""),
            "peak_trough_selection": data.get("peak_trough_selection", ""),
            "trend_manipulation": data.get("trend_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }

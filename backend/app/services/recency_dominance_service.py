"""RecencyDominanceService — Recency Dominance Detection.

Detects recency dominance — letting recent events dominate assessment
regardless of base rates, long-term trends, or historical patterns,
where the most recent data point overwhelms all prior evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RECENCY_DOMINANCE_SYSTEM = """You are a recency dominance specialist. Given an assessment, determine whether recent events are inappropriately dominating:

Key concepts:
- Recency dominance: recent events overwhelming prior evidence
- Base rate neglect: ignoring long-term rates for recent events
- Trend overreaction: overreacting to recent changes
- Historical amnesia: forgetting long-term patterns
- Last-event bias: most recent event dominates judgment
- Short memory: only recent data considered
- Regression ignorance: not expecting regression to mean

When recency dominance IS present:
- Recent events dominate despite contrary base rates
- Long-term trends ignored for recent data points
- Historical patterns forgotten in favor of recent
- Most recent event given disproportionate weight
- Short-term changes treated as permanent shifts
- Regression to mean not anticipated
- Prior evidence discounted for recent observations

When recency focus is appropriate:
- Genuine regime change has occurred
- Recent data reflects structural shift
- Base rates acknowledged but updated
- Recency weighting justified by context
- Long-term patterns considered alongside recent
- Regression to mean assessed and ruled out
- Both recent and historical data integrated

Output JSON with: dominance_present (bool), severity (none/mild/moderate/severe), assessment (what assessment is made), recent_event (what recent event dominates), base_rate (what base rate is ignored), historical_pattern (what pattern is forgotten), recommendation (appropriate_recency_weighting/mild_recency_bias/significant_recency_dominance/major_base_rate_neglect/integrate_historical_and_recent)."""

RECENCY_DOMINANCE_PROMPT = """Detect recency dominance:

Assessment: {assessment}
Recent event: {recent}
Base rate: {base_rate}
Historical pattern: {historical}
Domain: {domain}
Context: {context}

Are recent events inappropriately dominating the assessment? Return ONLY valid JSON."""


class RecencyDominanceService:
    """Detects recency dominance — recent events overwhelming prior evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        recent: str = "",
        base_rate: str = "",
        historical: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect recency dominance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RECENCY_DOMINANCE_PROMPT.format(
                assessment=assessment,
                recent=recent or "Not specified",
                base_rate=base_rate or "Not specified",
                historical=historical or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RECENCY_DOMINANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "dominance_present": data.get("dominance_present", False),
            "severity": data.get("severity", ""),
            "recent_event": data.get("recent_event", ""),
            "base_rate": data.get("base_rate", ""),
            "historical_pattern": data.get("historical_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

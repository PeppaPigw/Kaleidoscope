"""TemporalCherryPickingService — Temporal Cherry Picking Detection.

Detects temporal cherry picking — selecting time periods, start dates,
or end dates that support a desired narrative while ignoring periods
that would contradict it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_CHERRY_PICKING_SYSTEM = """You are a temporal cherry picking specialist. Given a time-based argument, assess whether time periods are being selectively chosen:

Key concepts:
- Temporal cherry picking: selecting periods that support narrative
- Start date manipulation: choosing start that favors conclusion
- End date manipulation: choosing end that favors conclusion
- Period selection bias: picking favorable time windows
- Trend manufacturing: creating trends through period selection
- Baseline gaming: choosing baselines that support claims
- Window dressing: selecting time windows for appearance

When temporal cherry picking IS present:
- Time periods selected to support desired conclusion
- Start or end dates chosen to favor narrative
- Unfavorable periods excluded without justification
- Trends manufactured through period selection
- Baselines chosen to make data look favorable
- Time windows selected for appearance not substance
- Full temporal picture would contradict the claim

When time period selection is appropriate:
- Period selection justified by research question
- Multiple time periods examined
- Sensitivity to period choice tested
- Full temporal context provided
- Period boundaries have substantive rationale
- Alternative periods acknowledged
- Robustness across periods demonstrated

Output JSON with: cherry_picking_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), period_selected (what period is chosen), period_excluded (what period is excluded), full_picture (what full temporal picture shows), recommendation (appropriate_period_selection/mild_period_bias/significant_temporal_cherry_picking/major_period_manipulation/examine_full_temporal_range)."""

TEMPORAL_CHERRY_PICKING_PROMPT = """Detect temporal cherry picking:

Claim: {claim}
Period selected: {period}
Justification for period: {justification}
Excluded periods: {excluded}
Domain: {domain}
Context: {context}

Are time periods being selectively chosen to support a narrative? Return ONLY valid JSON."""


class TemporalCherryPickingService:
    """Detects temporal cherry picking — selective time period choice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        period: str = "",
        justification: str = "",
        excluded: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect temporal cherry picking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_CHERRY_PICKING_PROMPT.format(
                claim=claim,
                period=period or "Not specified",
                justification=justification or "Not specified",
                excluded=excluded or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_CHERRY_PICKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "cherry_picking_present": data.get("cherry_picking_present", False),
            "severity": data.get("severity", ""),
            "period_selected": data.get("period_selected", ""),
            "period_excluded": data.get("period_excluded", ""),
            "full_picture": data.get("full_picture", ""),
            "recommendation": data.get("recommendation", ""),
        }

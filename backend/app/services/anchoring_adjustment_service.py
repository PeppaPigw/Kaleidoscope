"""AnchoringAdjustmentService — Anchoring Adjustment Insufficiency Detection.

Detects insufficient adjustment from anchors — when people
adjust from an initial anchor but stop too early, remaining
biased toward the anchor. Tversky & Kahneman (1974). Even
known-irrelevant anchors pull estimates. Adjustments are
typically insufficient because people stop when they reach
a plausible value rather than the correct one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANCHORING_ADJUSTMENT_SYSTEM = """You are an anchoring adjustment specialist. Given an estimate or judgment, assess whether the person has insufficiently adjusted from an initial anchor:

Key concepts (Tversky & Kahneman, 1974; Epley & Gilovich, 2006):
- Anchoring: initial values bias subsequent estimates
- Insufficient adjustment: people adjust from anchors but stop too early
- Plausibility stopping: adjustment stops at first plausible value, not correct one
- Irrelevant anchors: even random numbers bias estimates
- Self-generated anchors: starting from what you know and adjusting
- Anchor strength: stronger anchors produce less adjustment
- Effortful adjustment: adjustment requires cognitive effort and is often truncated

When insufficient adjustment IS present:
- Estimate suspiciously close to an initial reference point
- "Starting from X and adjusting" but the adjustment is too small
- Salary negotiations anchored by first offer
- Project estimates anchored by initial guess
- Valuations anchored by asking price rather than fundamentals
- Forecasts anchored by last period's numbers

When the estimate IS well-calibrated:
- The anchor is genuinely informative (base rate, historical data)
- Adjustment accounts for all known differences from the anchor
- The estimate is validated against independent methods
- Multiple starting points converge on the same estimate
- The person can articulate why the adjustment amount is correct

Output JSON with: insufficient_adjustment_present (bool), severity (none/mild/moderate/severe), estimate (what is being estimated), anchor (what is the initial anchor), adjustment_made (how much adjustment was made), adjustment_needed (how much adjustment was likely needed), anchor_relevance (is the anchor genuinely informative?), stopping_reason (why did adjustment stop where it did?), independent_estimate (what would an anchor-free estimate be?), confidence_in_estimate (how confident is the person?), recommendation (estimate_calibrated/mild_anchoring/significant_insufficient_adjustment/major_anchor_bias/re_estimate_from_scratch)."""

ANCHORING_ADJUSTMENT_PROMPT = """Detect insufficient anchoring adjustment:

Estimate: {estimate}
Anchor: {anchor}
Adjustment: {adjustment}
Method: {method}
Domain: {domain}
Context: {context}

Has the person insufficiently adjusted from the initial anchor? Return ONLY valid JSON."""


class AnchoringAdjustmentService:
    """Detects insufficient adjustment from anchors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        estimate: str,
        *,
        anchor: str = "",
        adjustment: str = "",
        method: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect insufficient anchoring adjustment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANCHORING_ADJUSTMENT_PROMPT.format(
                estimate=estimate,
                anchor=anchor or "Not specified",
                adjustment=adjustment or "Not specified",
                method=method or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ANCHORING_ADJUSTMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "estimate": estimate[:200],
            "insufficient_adjustment_present": data.get("insufficient_adjustment_present", False),
            "severity": data.get("severity", ""),
            "anchor": data.get("anchor", ""),
            "adjustment_made": data.get("adjustment_made", ""),
            "adjustment_needed": data.get("adjustment_needed", ""),
            "anchor_relevance": data.get("anchor_relevance", ""),
            "stopping_reason": data.get("stopping_reason", ""),
            "independent_estimate": data.get("independent_estimate", ""),
            "confidence_in_estimate": data.get("confidence_in_estimate", ""),
            "recommendation": data.get("recommendation", ""),
        }

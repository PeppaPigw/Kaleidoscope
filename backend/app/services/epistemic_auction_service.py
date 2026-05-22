"""EpistemicAuctionService — Epistemic Auction Detection.

Detects epistemic auction — intellectual attention and credibility being
allocated through competitive bidding mechanisms rather than merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUCTION_SYSTEM = """You are an epistemic auction specialist. Given an intellectual allocation pattern, assess whether competitive bidding replaces merit:

Key concepts:
- Epistemic auction: attention allocated by bidding not merit
- Winner's curse: winning bidder overpaying
- Reserve price: minimum acceptable bid
- Bid shading: bidding below true value strategically
- Common value: same underlying value for all
- Private value: different value for each bidder
- Revenue equivalence: different formats yielding same outcome

When epistemic auction IS present:
- Attention allocated through competitive bidding
- Winners overpaying for intellectual attention
- Minimum threshold for participation
- Strategic underbidding to avoid overpaying
- Same underlying truth value for all
- Different personal value for each participant
- Different allocation methods yielding same winners

When merit-based allocation is present:
- Attention allocated by quality and merit
- No overpaying for attention
- No minimum threshold beyond quality
- No strategic behavior needed
- Value determined by content quality
- Same evaluation criteria for all
- Allocation method matches merit

Output JSON with: auction_present (bool), severity (none/mild/moderate/severe), winners_curse (what overpaying), reserve_price (what minimum), bid_shading (what strategic underbidding), common_value (what shared truth), recommendation (merit_based/mild_auction/significant_auction/major_bidding_over_merit/restore_merit_allocation)."""

EPISTEMIC_AUCTION_PROMPT = """Detect epistemic auction:

Winners curse: {winners_curse}
Reserve price: {reserve_price}
Bid shading: {bid_shading}
Common value: {common_value}
Domain: {domain}
Context: {context}

Is intellectual attention and credibility being allocated through competitive bidding rather than merit? Return ONLY valid JSON."""


class EpistemicAuctionService:
    """Detects epistemic auction — attention allocated by bidding not merit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        winners_curse: str,
        *,
        reserve_price: str = "",
        bid_shading: str = "",
        common_value: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic auction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUCTION_PROMPT.format(
                winners_curse=winners_curse,
                reserve_price=reserve_price or "Not specified",
                bid_shading=bid_shading or "Not specified",
                common_value=common_value or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "winners_curse": winners_curse[:200],
            "auction_present": data.get("auction_present", False),
            "severity": data.get("severity", ""),
            "reserve_price": data.get("reserve_price", ""),
            "bid_shading": data.get("bid_shading", ""),
            "common_value": data.get("common_value", ""),
            "recommendation": data.get("recommendation", ""),
        }

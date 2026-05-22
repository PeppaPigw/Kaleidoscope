"""EndowmentEffectService — Endowment Effect Detection.

Detects the endowment effect — valuing something more simply
because you own it. Thaler (1980), Kahneman, Knetsch & Thaler
(1990). The mug you own is worth more to you than an identical
mug you don't own. Loss aversion applied to possessions.
Selling price exceeds buying price for the same item.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ENDOWMENT_SYSTEM = """You are an endowment effect specialist. Given a valuation or exchange decision, assess whether ownership is inflating perceived value:

Key concepts (Thaler 1980, Kahneman, Knetsch & Thaler 1990):
- Endowment effect: valuing owned items more than identical unowned items
- WTA/WTP gap: willingness to accept (sell) exceeds willingness to pay (buy)
- Loss aversion mechanism: giving up feels like a loss, which hurts more than equivalent gain
- Mere ownership: even brief ownership increases valuation
- Status quo bias overlap: preferring current state because change = loss
- IKEA effect overlap: but endowment is about ownership, not creation

When the endowment effect IS present:
- Refusing to sell at a price you wouldn't pay to buy
- Overvaluing current possessions relative to market value
- "I wouldn't sell this for less than X" when you'd never pay X for it
- Holding onto things because giving them up feels like a loss
- Difficulty trading even when the trade is objectively beneficial
- Emotional attachment inflating perceived monetary value

When high valuation IS warranted:
- The item has genuine sentimental value that can't be replaced
- Transaction costs make the WTA/WTP gap rational
- The item has appreciated in value since purchase
- Unique customization makes replacement genuinely costly
- The person would genuinely pay the asking price if they didn't own it

Output JSON with: endowment_effect_present (bool), severity (none/mild/moderate/severe), item (what is owned), owner_valuation (what the owner thinks it's worth), market_valuation (what others would pay), wta_wtp_gap (difference between selling and buying price), ownership_duration (how long has it been owned), loss_aversion_factor (how much does "giving up" hurt?), sentimental_value (is there genuine irreplaceable value?), replacement_cost (what would it cost to get an equivalent?), opportunity_cost (what is being foregone by holding?), rational_valuation (what should it be worth?), recommendation (valuation_fair/mild_endowment/significant_overvaluation/major_endowment_effect/value_at_market)."""

ENDOWMENT_PROMPT = """Detect endowment effect:

Item/asset: {item}
Owner's valuation: {valuation}
Market comparison: {market}
Ownership context: {ownership}
Domain: {domain}
Context: {context}

Is ownership inflating perceived value beyond what's rational? Return ONLY valid JSON."""


class EndowmentEffectService:
    """Detects endowment effect — ownership inflating perceived value."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        item: str,
        *,
        valuation: str = "",
        market: str = "",
        ownership: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect endowment effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ENDOWMENT_PROMPT.format(
                item=item,
                valuation=valuation or "Not specified",
                market=market or "Not specified",
                ownership=ownership or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ENDOWMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "item": item[:200],
            "endowment_effect_present": data.get("endowment_effect_present", False),
            "severity": data.get("severity", ""),
            "owner_valuation": data.get("owner_valuation", ""),
            "market_valuation": data.get("market_valuation", ""),
            "wta_wtp_gap": data.get("wta_wtp_gap", ""),
            "ownership_duration": data.get("ownership_duration", ""),
            "loss_aversion_factor": data.get("loss_aversion_factor", ""),
            "sentimental_value": data.get("sentimental_value", ""),
            "replacement_cost": data.get("replacement_cost", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "rational_valuation": data.get("rational_valuation", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""DecouplingEffectService — Decoupling Effect Detection.

Detects decoupling effect — separating the pain of payment
from the pleasure of consumption, leading to overspending.
Prelec & Loewenstein (1998). Credit cards decouple payment
from purchase. Subscriptions decouple cost from usage.
Prepayment decouples spending from enjoyment. When payment
doesn't feel connected to consumption, spending increases.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECOUPLING_SYSTEM = """You are a decoupling effect specialist. Given a spending or resource allocation decision, assess whether the separation of cost from consumption is leading to suboptimal decisions:

Key concepts (Prelec & Loewenstein, 1998):
- Decoupling: separating payment from consumption
- Payment depreciation: pain of payment fades over time
- Sunk cost decoupling: prepayment removes ongoing cost awareness
- Credit card effect: delayed payment reduces spending pain
- Subscription blindness: fixed cost removes per-use awareness
- Buffet effect: prepayment leads to overconsumption
- Mental accounting interaction: decoupled costs assigned to different accounts

When decoupling IS causing problems:
- Credit card spending exceeding what cash spending would be
- Subscriptions maintained without usage awareness
- Prepaid services overused or underused without cost consideration
- "It's already paid for" justifying wasteful consumption
- Spending more because payment is invisible or delayed
- Not tracking per-unit costs because of flat-rate pricing

When decoupling IS beneficial:
- It reduces transaction costs and friction appropriately
- The person maintains awareness of total spending
- Prepayment serves legitimate budgeting purposes
- The convenience genuinely outweighs the awareness cost
- The person periodically reviews decoupled costs

Output JSON with: decoupling_present (bool), severity (none/mild/moderate/severe), decision (what spending/consumption decision), payment_method (how is payment structured), consumption_pattern (how is consumption occurring), awareness_level (how aware is the person of per-unit cost?), spending_increase (how much more is being spent due to decoupling?), would_cash_differ (bool — would behavior differ with immediate payment?), total_cost_tracked (bool — is total spending monitored?), recommendation (decoupling_beneficial/mild_awareness_gap/significant_overspending/major_decoupling_blindness/reconnect_cost_to_consumption)."""

DECOUPLING_PROMPT = """Detect decoupling effect:

Decision: {decision}
Payment structure: {payment}
Consumption: {consumption}
Awareness: {awareness}
Domain: {domain}
Context: {context}

Is separation of payment from consumption leading to suboptimal decisions? Return ONLY valid JSON."""


class DecouplingEffectService:
    """Detects decoupling effect — payment-consumption separation causing overspending."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        payment: str = "",
        consumption: str = "",
        awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect decoupling effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECOUPLING_PROMPT.format(
                decision=decision,
                payment=payment or "Not specified",
                consumption=consumption or "Not specified",
                awareness=awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DECOUPLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "decoupling_present": data.get("decoupling_present", False),
            "severity": data.get("severity", ""),
            "payment_method": data.get("payment_method", ""),
            "consumption_pattern": data.get("consumption_pattern", ""),
            "awareness_level": data.get("awareness_level", ""),
            "spending_increase": data.get("spending_increase", ""),
            "would_cash_differ": data.get("would_cash_differ", False),
            "total_cost_tracked": data.get("total_cost_tracked", True),
            "recommendation": data.get("recommendation", ""),
        }

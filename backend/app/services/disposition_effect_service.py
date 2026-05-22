"""DispositionEffectService — Disposition Effect Detection.

Detects disposition effect — tendency to sell assets that have
increased in value while keeping assets that have dropped in
value. Shefrin & Statman (1985). "Sell winners, hold losers."
Driven by loss aversion and mental accounting. Leads to
suboptimal portfolio performance and tax inefficiency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISPOSITION_SYSTEM = """You are a disposition effect specialist. Given an investment or asset decision, assess whether someone is exhibiting the disposition effect:

Key concepts (Shefrin & Statman, 1985):
- Disposition effect: selling winners too early, holding losers too long
- Loss aversion interaction: reluctance to realize losses
- Mental accounting: each position evaluated in isolation
- Reference point: purchase price as anchor for gain/loss
- Pride seeking: desire to realize gains (feel smart)
- Regret avoidance: reluctance to admit mistakes (realize losses)
- Tax inefficiency: opposite of tax-loss harvesting
- Break-even effect: holding losers hoping to "get back to even"

When disposition effect IS present:
- Selling stocks that went up while holding those that went down
- "I can't sell at a loss" without fundamental reason to hold
- Taking profits quickly but letting losses run
- Evaluating positions relative to purchase price rather than prospects
- "I'll sell when I break even" as primary strategy
- Portfolio of losers accumulated over time
- Quick profit-taking on any gain

When the behavior IS rational:
- Selling winners for rebalancing or liquidity needs
- Holding losers because fundamentals support recovery
- Tax-motivated timing of sales
- The person evaluates forward-looking prospects, not past prices
- Position sizing justifies the hold/sell decision
- Mean reversion is empirically supported in the specific context

Output JSON with: disposition_effect_present (bool), severity (none/mild/moderate/severe), decision (what asset decision is being made), reference_point (what is the reference/purchase price), current_value (current value relative to reference), holding_reason (why is the position being held/sold), forward_looking (is the decision based on future prospects?), loss_realization (is there reluctance to realize losses?), pattern (is this a repeated pattern?), recommendation (decision_rational/mild_disposition/significant_loss_holding/major_disposition_effect/evaluate_forward_prospects)."""

DISPOSITION_PROMPT = """Detect disposition effect:

Decision: {decision}
Position: {position}
Performance: {performance}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is someone selling winners and holding losers due to disposition effect? Return ONLY valid JSON."""


class DispositionEffectService:
    """Detects disposition effect — selling winners too early, holding losers too long."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        position: str = "",
        performance: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect disposition effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISPOSITION_PROMPT.format(
                decision=decision,
                position=position or "Not specified",
                performance=performance or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "disposition_effect_present": data.get("disposition_effect_present", False),
            "severity": data.get("severity", ""),
            "reference_point": data.get("reference_point", ""),
            "current_value": data.get("current_value", ""),
            "holding_reason": data.get("holding_reason", ""),
            "forward_looking": data.get("forward_looking", ""),
            "loss_realization": data.get("loss_realization", ""),
            "pattern": data.get("pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

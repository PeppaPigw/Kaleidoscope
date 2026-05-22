"""LossAversionService — Loss Aversion Detection.

Detects loss aversion — losses loom larger than equivalent
gains. Kahneman & Tversky (1979). The pain of losing $100
is roughly twice the pleasure of gaining $100. Leads to
excessive risk aversion for gains, risk seeking for losses,
and status quo bias.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LOSS_AVERSION_SYSTEM = """You are a loss aversion specialist. Given a decision involving potential gains and losses, assess whether loss aversion is distorting the decision:

Key concepts (Kahneman & Tversky, 1979):
- Loss aversion: losses weighted ~2x more than equivalent gains
- Reference dependence: outcomes evaluated relative to reference point
- Endowment effect interaction: owning something shifts reference point
- Status quo bias interaction: change involves potential loss
- Risk aversion for gains: preferring certain smaller gain over risky larger gain
- Risk seeking for losses: preferring risky option to avoid certain loss
- Loss framing: how the choice is framed affects perceived losses

When loss aversion IS distorting decisions:
- Refusing a bet with positive expected value because of loss possibility
- Holding losing investments to avoid "realizing" the loss
- Demanding much more to sell something than willing to pay to buy it
- Avoiding beneficial changes because of small downside risk
- Overinsuring against small losses
- Refusing fair trades because giving up feels worse than receiving
- "I can't afford to lose" when the expected value is clearly positive

When the caution IS rational:
- The potential loss would cause genuine hardship (non-linear utility)
- The person has limited resources and can't absorb the loss
- The asymmetry reflects genuine asymmetric consequences
- Risk aversion is appropriate given the person's situation
- The expected value is actually negative or uncertain

Output JSON with: loss_aversion_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), potential_gain (what could be gained), potential_loss (what could be lost), expected_value (what is the expected value), loss_weight (how much more is the loss weighted), reference_point (what is the reference point), risk_capacity (can the person absorb the loss?), recommendation (caution_rational/mild_loss_aversion/significant_loss_overweighting/major_loss_aversion/reframe_as_portfolio)."""

LOSS_AVERSION_PROMPT = """Detect loss aversion:

Decision: {decision}
Gain: {gain}
Loss: {loss}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Is loss aversion distorting this decision beyond rational caution? Return ONLY valid JSON."""


class LossAversionService:
    """Detects loss aversion — losses weighted disproportionately more than gains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        gain: str = "",
        loss: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect loss aversion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LOSS_AVERSION_PROMPT.format(
                decision=decision,
                gain=gain or "Not specified",
                loss=loss or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LOSS_AVERSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "loss_aversion_present": data.get("loss_aversion_present", False),
            "severity": data.get("severity", ""),
            "potential_gain": data.get("potential_gain", ""),
            "potential_loss": data.get("potential_loss", ""),
            "expected_value": data.get("expected_value", ""),
            "loss_weight": data.get("loss_weight", ""),
            "reference_point": data.get("reference_point", ""),
            "risk_capacity": data.get("risk_capacity", ""),
            "recommendation": data.get("recommendation", ""),
        }

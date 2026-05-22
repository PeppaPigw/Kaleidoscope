"""HouseMoneyService — House Money Effect Detection.

Detects house money effect — tendency to take greater risks
with money that has been won or gained easily (perceived as
"house money") compared to money that was earned. Thaler &
Johnson (1990). Prior gains increase risk-seeking because
the gains feel like "free money" that can be gambled.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HOUSE_MONEY_SYSTEM = """You are a house money effect specialist. Given a risk-taking decision, assess whether prior gains are causing excessive risk-seeking:

Key concepts (Thaler & Johnson, 1990):
- House money effect: prior gains increase risk tolerance
- Mental accounting: gains segregated from "real" money
- Risk-seeking after gains: treating winnings as expendable
- Windfall effect: unexpected gains treated differently from earned income
- Integration failure: not integrating gains into total wealth
- Casino mentality: "playing with house money" justification
- Escalation after wins: increasing bet sizes after winning

When house money effect IS present:
- "I'm playing with house money" to justify risky bets
- Increasing risk after a windfall or unexpected gain
- Treating investment gains differently from principal
- "I can afford to lose it since I didn't earn it"
- Gambling more aggressively after winning
- Taking risks with bonus money that wouldn't be taken with salary
- "Easy come, easy go" attitude toward gains

When the risk-taking IS rational:
- Risk tolerance genuinely increased due to higher wealth
- The person treats all money fungibly regardless of source
- Risk-taking is proportional to total portfolio, not recent gains
- The decision would be the same regardless of how the money was obtained
- Increased risk is part of a deliberate rebalancing strategy

Output JSON with: house_money_present (bool), severity (none/mild/moderate/severe), decision (what risk decision is being made), prior_gain (what gain preceded this decision), gain_source (how was the money obtained), risk_level (how risky is the current decision), would_risk_without_gain (bool — would same risk be taken without prior gain?), mental_account (is the gain in a separate mental account?), total_wealth_considered (bool — is total wealth being considered?), recommendation (risk_rational/mild_house_money/significant_gain_driven_risk/major_house_money_effect/integrate_with_total_wealth)."""

HOUSE_MONEY_PROMPT = """Detect house money effect:

Decision: {decision}
Prior gain: {prior_gain}
Risk level: {risk_level}
Source: {source}
Domain: {domain}
Context: {context}

Are prior gains causing excessive risk-taking? Return ONLY valid JSON."""


class HouseMoneyService:
    """Detects house money effect — prior gains causing excessive risk-seeking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        prior_gain: str = "",
        risk_level: str = "",
        source: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect house money effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HOUSE_MONEY_PROMPT.format(
                decision=decision,
                prior_gain=prior_gain or "Not specified",
                risk_level=risk_level or "Not specified",
                source=source or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HOUSE_MONEY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "house_money_present": data.get("house_money_present", False),
            "severity": data.get("severity", ""),
            "prior_gain": data.get("prior_gain", ""),
            "gain_source": data.get("gain_source", ""),
            "risk_level": data.get("risk_level", ""),
            "would_risk_without_gain": data.get("would_risk_without_gain", False),
            "mental_account": data.get("mental_account", ""),
            "total_wealth_considered": data.get("total_wealth_considered", True),
            "recommendation": data.get("recommendation", ""),
        }

"""SunkCostAsymmetryService — Sunk Cost Asymmetry Detection.

Detects sunk cost asymmetry — when past investments (time, money,
effort) are weighted differently depending on whether the decision
involves potential gains or losses, leading to irrational
continuation of failing projects or premature abandonment of
promising ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SUNK_COST_ASYMMETRY_SYSTEM = """You are a sunk cost asymmetry specialist. Given a decision, assess whether past investments are irrationally influencing the choice:

Key concepts:
- Sunk cost fallacy: continuing because of past investment, not future value
- Asymmetric weighting: treating sunk costs differently for gains vs losses
- Escalation of commitment: doubling down on failing investments
- Prospective value: only future costs and benefits should matter
- Loss aversion interaction: sunk costs feel like losses if abandoned
- Concorde fallacy: continuing a project because of past investment
- Fresh start thinking: would you start this today if you hadn't already invested?

When sunk cost asymmetry IS present:
- "We've invested too much to stop now" (regardless of future prospects)
- Continuing a failing project because of past spending
- Refusing to cut losses because it would "waste" prior investment
- Asymmetric treatment: abandoning winners early but holding losers
- "We can't let that investment go to waste"
- Ignoring that past costs are irrecoverable regardless of decision
- Emotional attachment to past effort driving future decisions

When sunk cost asymmetry is NOT present:
- Decision is based on future expected value, not past investment
- Past investment is acknowledged but not weighted in the decision
- The "fresh start" test is applied (would you start this today?)
- Continuation is justified by future prospects, not past costs
- Switching costs (future costs of changing) are distinguished from sunk costs
- Learning from past investment informs but doesn't determine the decision
- Both continuation and abandonment are evaluated on future merits

Output JSON with: sunk_cost_asymmetry_present (bool), severity (none/mild/moderate/severe), investment (what has been invested), future_value (what future value exists), fresh_start_test (would you start this today), asymmetry (how are gains/losses treated differently), recommendation (no_sunk_cost_issue/mild_attachment/significant_sunk_cost_asymmetry/major_escalation/apply_fresh_start_test)."""

SUNK_COST_ASYMMETRY_PROMPT = """Detect sunk cost asymmetry:

Decision: {decision}
Past investment: {investment}
Future prospects: {prospects}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Are past investments irrationally influencing this decision? Return ONLY valid JSON."""


class SunkCostAsymmetryService:
    """Detects sunk cost asymmetry — irrational weighting of past investments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        investment: str = "",
        prospects: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sunk cost asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SUNK_COST_ASYMMETRY_PROMPT.format(
                decision=decision,
                investment=investment or "Not specified",
                prospects=prospects or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SUNK_COST_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "sunk_cost_asymmetry_present": data.get("sunk_cost_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "investment": data.get("investment", ""),
            "future_value": data.get("future_value", ""),
            "fresh_start_test": data.get("fresh_start_test", ""),
            "recommendation": data.get("recommendation", ""),
        }

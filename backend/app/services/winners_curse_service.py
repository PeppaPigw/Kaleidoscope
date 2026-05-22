"""WinnersCurseService — Winner's Curse Detection.

Detects the winner's curse — in competitive bidding/selection,
the winner tends to be the one who most overestimated the value.
Winning itself is evidence of overpayment. Applies to auctions,
hiring wars, M&A, competitive grants, and any situation where
the most optimistic estimate wins.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WINNERS_CURSE_SYSTEM = """You are a winner's curse specialist. Given a competitive situation, assess whether the winner's curse is likely:

Key concepts:
- In common-value auctions, the winner is the bidder who most overestimated
- Winning is itself evidence of overpayment (adverse selection on yourself)
- The more bidders, the worse the curse (more extreme the winning estimate)
- Applies beyond auctions: hiring wars, M&A, competitive grants, dating markets
- Rational bidders shade their bids down to account for the curse
- Inexperienced bidders are most vulnerable

Output JSON with: winners_curse_likely (bool), severity (none/mild/moderate/severe/extreme), competition_type (auction/bidding_war/hiring/acquisition/grant/other), number_of_competitors (how many are competing), value_uncertainty (how uncertain the true value is: low/moderate/high/extreme), winner_overpayment_estimate (how much the winner likely overpaid as percentage), common_value_component (0-1 — how much of the value is common vs private), information_asymmetry (who knows more about true value), experience_of_winner (naive/moderate/sophisticated), rational_bid_adjustment (how much a rational bidder should shade down), escalation_dynamics (what drives bids up beyond rational), exit_cost (cost of walking away from the competition), post_acquisition_regret_risk (0-1), who_benefits (who gains from the winner's curse — usually the seller), mitigation_strategies (how to avoid the curse), recommendation (no_curse_risk/mild_risk_proceed/significant_risk_shade_bid/high_risk_consider_walking/extreme_risk_exit)."""

WINNERS_CURSE_PROMPT = """Detect winner's curse:

Situation: {situation}
Competition: {competition}
Value uncertainty: {uncertainty}
Number of competitors: {competitors}
Domain: {domain}
Context: {context}

Is the winner's curse likely? Return ONLY valid JSON."""


class WinnersCurseService:
    """Detects winner's curse in competitive situations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        competition: str = "",
        uncertainty: str = "",
        competitors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect winner's curse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WINNERS_CURSE_PROMPT.format(
                situation=situation,
                competition=competition or "Not specified",
                uncertainty=uncertainty or "Not specified",
                competitors=competitors or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WINNERS_CURSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "winners_curse_likely": data.get("winners_curse_likely", False),
            "severity": data.get("severity", ""),
            "competition_type": data.get("competition_type", ""),
            "number_of_competitors": data.get("number_of_competitors", ""),
            "value_uncertainty": data.get("value_uncertainty", ""),
            "winner_overpayment_estimate": data.get("winner_overpayment_estimate", ""),
            "common_value_component": data.get("common_value_component", 0),
            "information_asymmetry": data.get("information_asymmetry", ""),
            "experience_of_winner": data.get("experience_of_winner", ""),
            "rational_bid_adjustment": data.get("rational_bid_adjustment", ""),
            "escalation_dynamics": data.get("escalation_dynamics", ""),
            "exit_cost": data.get("exit_cost", ""),
            "post_acquisition_regret_risk": data.get("post_acquisition_regret_risk", 0),
            "who_benefits": data.get("who_benefits", ""),
            "mitigation_strategies": data.get("mitigation_strategies", ""),
            "recommendation": data.get("recommendation", ""),
        }

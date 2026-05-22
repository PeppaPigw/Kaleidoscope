"""SkinInGameService — Skin in the Game Assessment.

Evaluates whether decision-makers bear the consequences of their
decisions. When those making decisions don't face downside risk,
they tend to make riskier, less careful choices. Identifies
asymmetric risk-bearing and accountability gaps.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SKIN_SYSTEM = """You are a skin-in-the-game specialist. Given a decision or system, assess whether decision-makers bear appropriate consequences:
- Do those making the decision face downside risk from bad outcomes?
- Is there asymmetry between who decides and who bears consequences?
- Can the decision-maker externalize costs while capturing benefits?
- Would the decision-maker behave differently if they had more skin in the game?
- Are there accountability mechanisms that create proxy skin in the game?

Output JSON with: skin_in_game_present (bool — do decision-makers bear consequences?), asymmetry_severity (none/mild/moderate/severe/extreme), decision_maker (who is deciding), risk_bearer (who bears the consequences), upside_capture (who gets benefits if it works), downside_exposure (who suffers if it fails), decision_maker_downside (what the decision-maker personally loses if wrong), decision_maker_upside (what they gain if right), moral_hazard_created (bool — does lack of skin enable reckless behavior?), accountability_mechanisms (existing mechanisms creating proxy accountability), missing_accountability (what accountability should exist but doesn't), historical_outcome (what happened when similar asymmetries existed), soul_in_game (bool — does the decision-maker have reputational/ethical stake beyond financial?), time_horizon_mismatch (bool — can decision-maker exit before consequences arrive?), transfer_of_fragility (bool — is fragility being transferred from strong to weak?), recommendation (aligned/add_accountability/restructure_incentives/refuse_asymmetry/accept_with_monitoring)."""

SKIN_PROMPT = """Assess skin in the game:

Decision/System: {decision}
Decision maker: {decision_maker}
Affected parties: {affected_parties}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Do decision-makers have skin in the game? Return ONLY valid JSON."""


class SkinInGameService:
    """Assesses whether decision-makers bear consequences of their decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        decision: str,
        *,
        decision_maker: str = "",
        affected_parties: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess skin in the game."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SKIN_PROMPT.format(
                decision=decision,
                decision_maker=decision_maker or "Not specified",
                affected_parties=affected_parties or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SKIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "skin_in_game_present": data.get("skin_in_game_present", False),
            "asymmetry_severity": data.get("asymmetry_severity", ""),
            "decision_maker": data.get("decision_maker", ""),
            "risk_bearer": data.get("risk_bearer", ""),
            "upside_capture": data.get("upside_capture", ""),
            "downside_exposure": data.get("downside_exposure", ""),
            "decision_maker_downside": data.get("decision_maker_downside", ""),
            "decision_maker_upside": data.get("decision_maker_upside", ""),
            "moral_hazard_created": data.get("moral_hazard_created", False),
            "accountability_mechanisms": data.get("accountability_mechanisms", ""),
            "missing_accountability": data.get("missing_accountability", ""),
            "historical_outcome": data.get("historical_outcome", ""),
            "soul_in_game": data.get("soul_in_game", False),
            "time_horizon_mismatch": data.get("time_horizon_mismatch", False),
            "transfer_of_fragility": data.get("transfer_of_fragility", False),
            "recommendation": data.get("recommendation", ""),
        }

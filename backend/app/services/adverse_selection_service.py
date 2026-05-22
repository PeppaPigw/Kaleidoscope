"""AdverseSelectionService — Adverse Selection Detection.

Detects adverse selection — when information asymmetry causes
market failure because one party knows more than the other.
Akerlof's "Market for Lemons" (1970). Sellers of bad products
stay in the market while sellers of good products exit, driving
down average quality. Applies to insurance, hiring, dating,
used goods, and any market with hidden information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ADVERSE_SYSTEM = """You are an adverse selection specialist. Given a market or selection situation, assess whether adverse selection is degrading quality:

Key concepts (Akerlof, 1970 — "Market for Lemons"):
- Adverse selection: informed party self-selects in ways that harm the uninformed party
- Information asymmetry: one side knows more about quality than the other
- Lemons problem: bad products drive out good products
- Death spiral: adverse selection → price increase → more adverse selection
- Signaling: costly actions to credibly reveal private information (Spence, 1973)
- Screening: mechanisms to induce self-revelation of type

Classic examples:
- Insurance: sick people buy more insurance → premiums rise → healthy people leave
- Used cars: sellers know defects, buyers don't → buyers assume worst → good cars leave market
- Hiring: bad candidates apply everywhere, good candidates are selective
- Lending: risky borrowers seek loans most aggressively

When adverse selection IS present:
- One party has private information about quality
- Self-selection is occurring based on that information
- Average quality is declining over time
- Good types are exiting or not participating
- Price/terms don't differentiate quality levels

Countermeasures:
- Signaling (costly credible signals of quality)
- Screening (mechanisms that separate types)
- Warranties/guarantees (skin in the game)
- Reputation systems
- Mandatory disclosure
- Pooling with verification

Output JSON with: adverse_selection_present (bool), severity (none/mild/moderate/severe), information_asymmetry (what one party knows that the other doesn't), informed_party (who has the information advantage), uninformed_party (who is at a disadvantage), self_selection_pattern (how informed parties are self-selecting), quality_degradation (how average quality is affected), death_spiral_risk (bool — is there a feedback loop?), signaling_available (what credible signals could reveal quality), screening_possible (what mechanisms could separate types), market_unraveling (bool — are good types exiting?), countermeasures_in_place (what protections exist), countermeasures_needed (what additional protections would help), pooling_vs_separating (is the market pooling different quality levels?), welfare_loss (what value is being destroyed), recommendation (no_adverse_selection/mild_information_gap/significant_adverse_selection/severe_market_failure/implement_screening_urgently)."""

ADVERSE_PROMPT = """Detect adverse selection:

Situation: {situation}
Market/Selection: {market}
Information distribution: {information}
Quality signals: {signals}
Domain: {domain}
Context: {context}

Is adverse selection degrading quality in this market? Return ONLY valid JSON."""


class AdverseSelectionService:
    """Detects adverse selection — information asymmetry causing quality degradation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        market: str = "",
        information: str = "",
        signals: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect adverse selection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ADVERSE_PROMPT.format(
                situation=situation,
                market=market or "Not specified",
                information=information or "Not specified",
                signals=signals or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ADVERSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "adverse_selection_present": data.get("adverse_selection_present", False),
            "severity": data.get("severity", ""),
            "information_asymmetry": data.get("information_asymmetry", ""),
            "informed_party": data.get("informed_party", ""),
            "uninformed_party": data.get("uninformed_party", ""),
            "self_selection_pattern": data.get("self_selection_pattern", ""),
            "quality_degradation": data.get("quality_degradation", ""),
            "death_spiral_risk": data.get("death_spiral_risk", False),
            "signaling_available": data.get("signaling_available", ""),
            "screening_possible": data.get("screening_possible", ""),
            "market_unraveling": data.get("market_unraveling", False),
            "countermeasures_in_place": data.get("countermeasures_in_place", ""),
            "countermeasures_needed": data.get("countermeasures_needed", ""),
            "pooling_vs_separating": data.get("pooling_vs_separating", ""),
            "welfare_loss": data.get("welfare_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }

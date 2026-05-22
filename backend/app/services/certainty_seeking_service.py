"""CertaintySeekingService — Certainty Seeking Detection.

Detects certainty seeking — preferring certain but inferior outcomes
over uncertain but superior ones beyond what rational risk aversion
justifies, paying excessive premiums for certainty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CERTAINTY_SEEKING_SYSTEM = """You are a certainty seeking specialist. Given a decision, assess whether certainty is being overvalued relative to expected value:

Key concepts:
- Certainty seeking: overvaluing certain outcomes
- Certainty premium: paying too much for guaranteed outcomes
- Allais paradox: preference reversals involving certainty
- Risk aversion excess: avoiding risk beyond rational levels
- Ambiguity aversion: preferring known risks to unknown ones
- Certainty illusion: treating high probability as certainty
- Expected value neglect: ignoring EV in favor of certainty

When certainty seeking IS present:
- Certain inferior outcome chosen over uncertain superior one
- Premium paid for certainty exceeds rational risk aversion
- Expected value significantly sacrificed for certainty
- Ambiguity avoided even when expected value is higher
- Small probability of loss preventing large expected gain
- Certainty treated as qualitatively different from high probability
- Risk aversion beyond what stakes justify

When certainty preference is appropriate:
- Stakes genuinely justify risk aversion (ruin scenarios)
- Certainty premium proportionate to actual risk
- Expected value difference small relative to certainty value
- Irreversibility makes certainty genuinely more valuable
- Risk tolerance appropriately calibrated to situation
- Certainty preference reflects genuine utility function
- Downside risk genuinely catastrophic

Output JSON with: seeking_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), certain_option (the certain but inferior option), uncertain_option (the uncertain but superior option), premium_paid (what is sacrificed for certainty), recommendation (appropriate_risk_aversion/mild_certainty_preference/significant_certainty_seeking/major_expected_value_neglect/accept_calibrated_uncertainty)."""

CERTAINTY_SEEKING_PROMPT = """Detect certainty seeking:

Decision: {decision}
Certain option: {certain}
Uncertain option: {uncertain}
Expected values: {values}
Domain: {domain}
Context: {context}

Is certainty being overvalued relative to expected value? Return ONLY valid JSON."""


class CertaintySeekingService:
    """Detects certainty seeking — overvaluing certain outcomes beyond rational risk aversion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        certain: str = "",
        uncertain: str = "",
        values: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect certainty seeking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CERTAINTY_SEEKING_PROMPT.format(
                decision=decision,
                certain=certain or "Not specified",
                uncertain=uncertain or "Not specified",
                values=values or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CERTAINTY_SEEKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "seeking_present": data.get("seeking_present", False),
            "severity": data.get("severity", ""),
            "certain_option": data.get("certain_option", ""),
            "uncertain_option": data.get("uncertain_option", ""),
            "premium_paid": data.get("premium_paid", ""),
            "recommendation": data.get("recommendation", ""),
        }

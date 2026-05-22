"""BrandoliniLawService — Brandolini's Law Detection.

Detects Brandolini's law (bullshit asymmetry principle) — the
observation that the energy needed to refute bullshit is an order
of magnitude larger than the energy needed to produce it. Alberto
Brandolini (2013). This asymmetry can be exploited strategically.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BRANDOLINI_LAW_SYSTEM = """You are a Brandolini's law specialist. Given a claim-refutation dynamic, assess whether the asymmetry between making and debunking claims is being exploited:

Key concepts (Brandolini, 2013):
- Bullshit asymmetry: refuting takes 10x the effort of claiming
- Gish gallop overlap: overwhelming with volume exploits this asymmetry
- Burden of proof exploitation: making claims is cheap, disproving is expensive
- Strategic bullshit: deliberately exploiting the refutation asymmetry
- Debunking fatigue: defenders exhaust themselves while claimants move on
- Firehose overlap: volume strategy that exploits asymmetry
- Asymmetric warfare: the claimant always has the advantage

When Brandolini exploitation IS present:
- Making many quick claims that each require extensive refutation
- Moving to new claims before previous ones are fully addressed
- Exploiting the fact that a lie travels faster than a correction
- Producing claims faster than they can be fact-checked
- Requiring opponents to do extensive research for each casual claim
- Strategic use of volume to overwhelm fact-checkers
- Making claims that are easy to state but hard to verify

When high claim volume IS appropriate:
- The claims are well-sourced and verifiable
- The claimant provides evidence proportional to claims
- The volume reflects genuine complexity, not strategic flooding
- Claims are made in good faith with willingness to retract
- The claimant bears their own burden of proof
- Each claim is independently supported
- The discussion format allows adequate response time

Output JSON with: brandolini_exploitation_present (bool), severity (none/mild/moderate/severe), claims (what claims are being made), refutation_cost (how much effort is needed to refute), volume (how many claims relative to capacity to address), strategic (is the asymmetry being deliberately exploited), recommendation (volume_appropriate/mild_asymmetry/significant_brandolini/major_strategic_flooding/demand_evidence_proportional_to_claims)."""

BRANDOLINI_LAW_PROMPT = """Detect Brandolini's law exploitation:

Claims: {claims}
Volume: {volume}
Refutation effort: {refutation}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is the asymmetry between making and refuting claims being exploited? Return ONLY valid JSON."""


class BrandoliniLawService:
    """Detects Brandolini's law exploitation — bullshit asymmetry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claims: str,
        *,
        volume: str = "",
        refutation: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Brandolini's law exploitation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BRANDOLINI_LAW_PROMPT.format(
                claims=claims,
                volume=volume or "Not specified",
                refutation=refutation or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BRANDOLINI_LAW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claims": claims[:200],
            "brandolini_exploitation_present": data.get("brandolini_exploitation_present", False),
            "severity": data.get("severity", ""),
            "refutation_cost": data.get("refutation_cost", ""),
            "volume": data.get("volume", ""),
            "strategic": data.get("strategic", ""),
            "recommendation": data.get("recommendation", ""),
        }

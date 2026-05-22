"""EpistemicInsoucianceService — Epistemic Insouciance Detection.

Detects epistemic insouciance — casual indifference to truth,
evidence, and knowledge quality, where getting things right
simply doesn't matter to the person making claims.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSOUCIANCE_SYSTEM = """You are an epistemic insouciance specialist. Given a knowledge claim, assess whether the claimant shows indifference to truth:

Key concepts:
- Epistemic insouciance: casual indifference to truth
- Bullshit (Frankfurt): speech indifferent to truth/falsity
- Careless assertion: claiming without checking
- Truth indifference: not caring whether claims are accurate
- Epistemic negligence: failing to exercise due care
- Casual falsehood: lying without even trying to deceive
- Post-truth attitude: truth simply doesn't matter

When epistemic insouciance IS present:
- Claims made without concern for accuracy
- Truth or falsity irrelevant to claimant
- No effort to verify before asserting
- Indifference to whether claims are correct
- Epistemic standards simply not applied
- Casual relationship with truth
- Getting it right doesn't matter

When casual communication is appropriate:
- Context clearly informal and non-consequential
- Claims not relied upon for decisions
- Audience understands informal nature
- No harm from inaccuracy in context
- Playful or hypothetical framing clear
- Stakes genuinely low
- No pretense of authority

Output JSON with: insouciance_present (bool), severity (none/mild/moderate/severe), claim (what claim is made), indifference (what indifference to truth exists), effort (what verification effort was made), stakes (what stakes exist), recommendation (appropriate_casual_communication/mild_carelessness/significant_epistemic_insouciance/major_truth_indifference/care_about_truth)."""

EPISTEMIC_INSOUCIANCE_PROMPT = """Detect epistemic insouciance:

Claim: {claim}
Verification effort: {effort}
Stakes: {stakes}
Attitude toward accuracy: {attitude}
Domain: {domain}
Context: {context}

Does the claimant show casual indifference to whether their claims are true? Return ONLY valid JSON."""


class EpistemicInsoucianceService:
    """Detects epistemic insouciance — casual indifference to truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        effort: str = "",
        stakes: str = "",
        attitude: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic insouciance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSOUCIANCE_PROMPT.format(
                claim=claim,
                effort=effort or "Not specified",
                stakes=stakes or "Not specified",
                attitude=attitude or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSOUCIANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "insouciance_present": data.get("insouciance_present", False),
            "severity": data.get("severity", ""),
            "indifference": data.get("indifference", ""),
            "effort": data.get("effort", ""),
            "stakes": data.get("stakes", ""),
            "recommendation": data.get("recommendation", ""),
        }

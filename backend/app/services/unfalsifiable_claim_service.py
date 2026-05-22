"""UnfalsifiableClaimService — Unfalsifiable Claim Detection.

Detects unfalsifiable claims — claims structured to be immune
from disconfirmation, making them untestable and therefore
uninformative about the world.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNFALSIFIABLE_CLAIM_SYSTEM = """You are an unfalsifiability specialist. Given a claim, assess whether it is structured to be immune from disconfirmation:

Key concepts:
- Unfalsifiability: no possible observation could disprove the claim
- Moving goalposts: redefining success after failure
- Immunizing strategies: built-in escape hatches for any counter-evidence
- Tautology: true by definition, not by evidence
- Vagueness as shield: claim too vague to test
- Retroactive explanation: can explain any outcome after the fact
- Heads-I-win-tails-you-lose: claim confirmed regardless of outcome

When unfalsifiability IS present:
- No conceivable evidence could disprove the claim
- Claim has built-in explanations for any counter-evidence
- Success criteria undefined or infinitely flexible
- Claim is tautological or definitionally true
- Vagueness prevents any specific test
- Any outcome interpreted as confirmation
- Auxiliary hypotheses added to absorb contradictions

When claims are falsifiable:
- Specific predictions that could be wrong
- Clear success/failure criteria defined
- Possible counter-evidence identified
- Claim makes risky predictions
- Testable implications specified
- Failure conditions acknowledged
- Precise enough to be wrong

Output JSON with: unfalsifiable (bool), severity (none/mild/moderate/severe), claim (what is claimed), immunizing_strategy (how claim avoids refutation), test_proposed (what would disprove it), vagueness (how vagueness shields from testing), recommendation (falsifiable_claim/mild_vagueness/significant_immunization/major_unfalsifiability/specify_failure_conditions)."""

UNFALSIFIABLE_CLAIM_PROMPT = """Detect unfalsifiable claims:

Claim: {claim}
Evidence cited: {evidence}
Counter-evidence response: {counter_response}
Predictions made: {predictions}
Domain: {domain}
Context: {context}

Is this claim structured to be immune from disconfirmation? Return ONLY valid JSON."""


class UnfalsifiableClaimService:
    """Detects unfalsifiable claims — immune from disconfirmation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        counter_response: str = "",
        predictions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect unfalsifiable claims."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNFALSIFIABLE_CLAIM_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                counter_response=counter_response or "Not specified",
                predictions=predictions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNFALSIFIABLE_CLAIM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "unfalsifiable": data.get("unfalsifiable", False),
            "severity": data.get("severity", ""),
            "immunizing_strategy": data.get("immunizing_strategy", ""),
            "test_proposed": data.get("test_proposed", ""),
            "vagueness": data.get("vagueness", ""),
            "recommendation": data.get("recommendation", ""),
        }

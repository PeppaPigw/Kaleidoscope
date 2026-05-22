"""UnfalsifiableFramingService — Unfalsifiable Framing Detection.

Detects unfalsifiable framing — structuring claims so they cannot
be tested, refuted, or disconfirmed by any possible evidence,
rendering them immune to empirical challenge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNFALSIFIABLE_FRAMING_SYSTEM = """You are an unfalsifiable framing specialist. Given a claim, assess whether it is structured to be immune to refutation:

Key concepts:
- Unfalsifiable framing: claims structured to resist all evidence
- Immunizing strategies: moves that protect claims from testing
- Heads-I-win framing: any outcome interpreted as confirmation
- Vague enough to survive: imprecision preventing disconfirmation
- Moving target: claim shifts to avoid refutation
- Retroactive reinterpretation: reframing after disconfirmation
- Untestable by design: deliberately avoiding testability

When unfalsifiable framing IS present:
- No possible evidence could disconfirm the claim
- Any outcome is interpreted as supporting the claim
- Claim is too vague to generate testable predictions
- Claim shifts meaning when challenged
- Disconfirming evidence is retroactively reinterpreted
- Claim is deliberately structured to avoid testing
- Immunizing strategies actively employed

When non-falsifiability is appropriate:
- Claim is definitional or analytic (not empirical)
- Claim is explicitly value-based or normative
- Claim is acknowledged as unfalsifiable framework
- Claim is clearly metaphorical or heuristic
- Limitations of testability explicitly stated
- Claim is preliminary and awaiting operationalization
- Domain genuinely lacks testable formulations yet

Output JSON with: unfalsifiable_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), strategy (how unfalsifiability is achieved), test (what would test it if properly framed), evasion (how refutation is evaded), recommendation (appropriately_non_empirical/mild_vagueness/significant_unfalsifiable_framing/major_immunization_strategy/make_claims_testable)."""

UNFALSIFIABLE_FRAMING_PROMPT = """Detect unfalsifiable framing:

Claim: {claim}
Evidence offered: {evidence}
Potential disconfirmation: {disconfirmation}
Response to challenge: {response}
Domain: {domain}
Context: {context}

Is this claim structured to be immune to refutation? Return ONLY valid JSON."""


class UnfalsifiableFramingService:
    """Detects unfalsifiable framing — claims immune to refutation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        disconfirmation: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect unfalsifiable framing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNFALSIFIABLE_FRAMING_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                disconfirmation=disconfirmation or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNFALSIFIABLE_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "unfalsifiable_present": data.get("unfalsifiable_present", False),
            "severity": data.get("severity", ""),
            "strategy": data.get("strategy", ""),
            "test": data.get("test", ""),
            "evasion": data.get("evasion", ""),
            "recommendation": data.get("recommendation", ""),
        }

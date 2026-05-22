"""AppealToIgnoranceService — Appeal to Ignorance Detection.

Detects appeal to ignorance (argumentum ad ignorantiam) — arguing
that something is true because it hasn't been proven false, or
false because it hasn't been proven true. Absence of evidence
is treated as evidence of absence (or presence).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_IGNORANCE_SYSTEM = """You are an appeal to ignorance specialist. Given an argument, assess whether it treats lack of evidence as proof:

Key concepts:
- Argumentum ad ignorantiam: absence of proof ≠ proof of absence
- Burden of proof: who must provide evidence?
- Negative proof: difficulty of proving a negative
- Absence of evidence vs evidence of absence: important distinction
- Default position: what to believe when evidence is lacking
- Unfalsifiable claims: claims that can't be disproven aren't proven
- Bayesian reasoning: absence of expected evidence IS informative

When appeal to ignorance IS present:
- "No one has proven X false, therefore X is true"
- "No one has proven X true, therefore X is false"
- Shifting burden of proof to the skeptic
- "You can't prove it DIDN'T happen"
- Treating unfalsifiability as evidence
- "Science hasn't explained X, therefore supernatural"
- Demanding proof of a negative as if it were easy

When appeal to ignorance is NOT present:
- Absence of evidence where evidence WOULD be expected (evidence of absence)
- Thorough search has been conducted and nothing found
- The claim is about what we currently know (epistemic humility)
- Burden of proof is correctly assigned
- The argument is about probability given current evidence
- Bayesian update: expected evidence not found reduces probability
- Acknowledging that lack of proof ≠ disproof, just uncertainty

Output JSON with: appeal_to_ignorance_present (bool), severity (none/mild/moderate/severe), claim (what is argued), ignorance_cited (what lack of evidence is cited), burden_of_proof (who should bear it), search_conducted (has evidence been sought), recommendation (no_appeal_to_ignorance/mild_burden_shift/significant_appeal_to_ignorance/major_proof_from_ignorance/assign_burden_correctly)."""

APPEAL_IGNORANCE_PROMPT = """Detect appeal to ignorance:

Argument: {argument}
Claim: {claim}
Evidence status: {evidence_status}
Burden of proof: {burden}
Domain: {domain}
Context: {context}

Does this treat lack of evidence as proof of something? Return ONLY valid JSON."""


class AppealToIgnoranceService:
    """Detects appeal to ignorance — treating absence of proof as proof."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        claim: str = "",
        evidence_status: str = "",
        burden: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_IGNORANCE_PROMPT.format(
                argument=argument,
                claim=claim or "Not specified",
                evidence_status=evidence_status or "Not specified",
                burden=burden or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_ignorance_present": data.get("appeal_to_ignorance_present", False),
            "severity": data.get("severity", ""),
            "claim": data.get("claim", ""),
            "ignorance_cited": data.get("ignorance_cited", ""),
            "burden_of_proof": data.get("burden_of_proof", ""),
            "recommendation": data.get("recommendation", ""),
        }

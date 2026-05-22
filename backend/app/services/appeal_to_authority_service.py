"""AppealToAuthorityService — Appeal to Authority Detection.

Detects appeal to authority (argumentum ad verecundiam) — citing
an authority figure as evidence when that authority is not an
expert in the relevant domain, or when expert opinion is used
as a substitute for evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_AUTHORITY_SYSTEM = """You are an appeal to authority specialist. Given an argument, assess whether it inappropriately relies on authority rather than evidence:

Key concepts:
- Argumentum ad verecundiam: inappropriate appeal to authority
- Relevant expertise: is the authority actually expert in THIS domain?
- Expert consensus vs individual opinion: one expert ≠ the field
- Authority as heuristic: sometimes deferring to experts IS rational
- Credentials vs evidence: credentials support but don't replace evidence
- Scope of expertise: experts outside their domain are laypeople
- Manufactured authority: creating false impression of expertise

When appeal to authority IS present:
- Citing a celebrity or public figure on a technical matter
- "Dr. X says so" when Dr. X's expertise is in an unrelated field
- Using authority as a substitute for presenting evidence
- "Nobel laureate says..." on a topic outside their Nobel field
- Treating one expert's opinion as settling a contested question
- Using credentials to shut down legitimate questioning
- Citing authority when the claim is empirically testable

When appeal to authority is NOT present:
- Citing experts within their domain of expertise
- Expert opinion used alongside evidence, not instead of it
- Acknowledging that expert opinion is probabilistic, not certain
- Citing scientific consensus (not just one authority)
- Deferring to expertise on genuinely complex technical matters
- Using expert guidance as a starting point for investigation
- Authority cited for factual claims that are verifiable

Output JSON with: appeal_to_authority_present (bool), severity (none/mild/moderate/severe), authority_cited (who is cited), domain_of_expertise (their actual expertise), domain_of_claim (what they're opining on), relevance (is their expertise relevant), evidence_available (is there direct evidence instead), recommendation (no_appeal_to_authority/mild_overreliance/significant_appeal_to_authority/major_authority_substitution/cite_evidence_directly)."""

APPEAL_AUTHORITY_PROMPT = """Detect appeal to authority:

Argument: {argument}
Authority cited: {authority}
Their expertise: {expertise}
Claim domain: {claim_domain}
Evidence available: {evidence}
Domain: {domain}
Context: {context}

Does this inappropriately rely on authority rather than evidence? Return ONLY valid JSON."""


class AppealToAuthorityService:
    """Detects appeal to authority — inappropriate reliance on authority over evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        authority: str = "",
        expertise: str = "",
        claim_domain: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to authority."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_AUTHORITY_PROMPT.format(
                argument=argument,
                authority=authority or "Not specified",
                expertise=expertise or "Not specified",
                claim_domain=claim_domain or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_AUTHORITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_authority_present": data.get("appeal_to_authority_present", False),
            "severity": data.get("severity", ""),
            "authority_cited": data.get("authority_cited", ""),
            "domain_of_expertise": data.get("domain_of_expertise", ""),
            "domain_of_claim": data.get("domain_of_claim", ""),
            "recommendation": data.get("recommendation", ""),
        }

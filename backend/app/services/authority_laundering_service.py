"""AuthorityLaunderingService — Authority Laundering Detection.

Detects authority laundering — passing claims through authority
figures or institutions to gain unearned credibility, where the
authority's endorsement substitutes for independent verification.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTHORITY_LAUNDERING_SYSTEM = """You are an authority laundering specialist. Given a claim, assess whether authority is being used to launder credibility:

Key concepts:
- Authority laundering: using authority to bypass verification
- Credibility transfer: borrowing credibility without earning it
- Endorsement substitution: endorsement replacing evidence
- Institutional pass-through: institution used as credibility vehicle
- Expert shopping: finding any expert who agrees
- Authority stacking: multiple authorities cited without substance
- Prestige borrowing: using prestige instead of argument

When authority laundering IS present:
- Claims gain credibility solely through authority association
- Authority endorsement substitutes for evidence
- Institutional prestige used to bypass scrutiny
- Expert agreement cited without examining reasoning
- Multiple authorities stacked without substance
- Credibility borrowed rather than earned through evidence
- Authority used to short-circuit verification

When authority citation is appropriate:
- Authority cited alongside evidence and reasoning
- Expert opinion used to supplement, not replace, evidence
- Institutional backing reflects genuine review process
- Authority's relevant expertise acknowledged and bounded
- Citation includes reasoning, not just endorsement
- Multiple sources reflect genuine convergence
- Authority used to guide inquiry, not end it

Output JSON with: laundering_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), authority_used (what authority is invoked), evidence_bypassed (what evidence is skipped), credibility_source (where credibility actually comes from), recommendation (appropriate_authority_citation/mild_over_reliance/significant_authority_laundering/major_credibility_bypass/provide_evidence_alongside_authority)."""

AUTHORITY_LAUNDERING_PROMPT = """Detect authority laundering:

Claim: {claim}
Authority cited: {authority}
Evidence provided: {evidence}
Verification done: {verification}
Domain: {domain}
Context: {context}

Is authority being used to launder credibility without proper evidence? Return ONLY valid JSON."""


class AuthorityLaunderingService:
    """Detects authority laundering — using authority to bypass verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        authority: str = "",
        evidence: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect authority laundering."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTHORITY_LAUNDERING_PROMPT.format(
                claim=claim,
                authority=authority or "Not specified",
                evidence=evidence or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTHORITY_LAUNDERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "laundering_present": data.get("laundering_present", False),
            "severity": data.get("severity", ""),
            "authority_used": data.get("authority_used", ""),
            "evidence_bypassed": data.get("evidence_bypassed", ""),
            "credibility_source": data.get("credibility_source", ""),
            "recommendation": data.get("recommendation", ""),
        }

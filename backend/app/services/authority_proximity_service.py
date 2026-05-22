"""AuthorityProximityService — Authority Proximity Bias Detection.

Detects authority proximity bias — giving more weight to claims
based on proximity to authority figures rather than evidence quality,
confusing social distance from authority with epistemic reliability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTHORITY_PROXIMITY_SYSTEM = """You are an authority proximity bias specialist. Given a claim evaluation, assess whether weight is being assigned based on proximity to authority rather than evidence:

Key concepts:
- Authority proximity: weight based on closeness to authority
- Reflected credibility: borrowing credibility from association
- Chain of authority: claims gaining weight through authority chains
- Name-dropping epistemology: citing authorities rather than evidence
- Institutional halo: institution's prestige transferred to claims
- Proximity fallacy: nearness to expert confused with expertise
- Authority cascade: authority flowing through social networks

When authority proximity bias IS present:
- Claims weighted by who said them, not evidence
- Proximity to authority treated as evidence
- Institutional affiliation substitutes for argument
- Name-dropping used instead of reasoning
- Social distance from authority determines credibility
- Reflected prestige treated as epistemic warrant
- Chain of authority replaces chain of evidence

When authority consideration is appropriate:
- Expert testimony used alongside evidence
- Authority cited for specific domain expertise
- Institutional backing reflects genuine quality control
- Authority used as heuristic with awareness of limits
- Claims evaluated on merits regardless of source
- Authority as starting point, not endpoint
- Expertise relevant to specific claim

Output JSON with: proximity_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), authority_cited (what authority is invoked), proximity_type (how proximity is established), evidence_gap (what evidence is missing), recommendation (appropriate_authority_use/mild_proximity_reliance/significant_authority_proximity/major_evidence_substitution/evaluate_on_evidence)."""

AUTHORITY_PROXIMITY_PROMPT = """Detect authority proximity bias:

Claim: {claim}
Authority cited: {authority}
Evidence provided: {evidence}
Proximity type: {proximity}
Domain: {domain}
Context: {context}

Is weight being assigned based on proximity to authority rather than evidence quality? Return ONLY valid JSON."""


class AuthorityProximityService:
    """Detects authority proximity bias — weight based on closeness to authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        authority: str = "",
        evidence: str = "",
        proximity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect authority proximity bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTHORITY_PROXIMITY_PROMPT.format(
                claim=claim,
                authority=authority or "Not specified",
                evidence=evidence or "Not specified",
                proximity=proximity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTHORITY_PROXIMITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "proximity_present": data.get("proximity_present", False),
            "severity": data.get("severity", ""),
            "authority_cited": data.get("authority_cited", ""),
            "proximity_type": data.get("proximity_type", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }

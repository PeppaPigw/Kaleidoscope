"""AuthorityBiasService — Authority Bias Detection.

Detects authority bias — accepting claims because of who said
them (credentials, status, fame) rather than the quality of
evidence or reasoning. Milgram's obedience experiments showed
how far people will go when an authority figure directs them.
Related to epistemic trespass but focused on the receiver's
uncritical acceptance rather than the speaker's overreach.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTHORITY_SYSTEM = """You are an authority bias specialist. Given a claim and its source, assess whether authority bias is inflating credibility:

Key concepts:
- Appeal to authority (argumentum ad verecundiam): using authority as evidence
- Legitimate vs illegitimate authority: is the authority relevant to the claim?
- Halo effect: expertise in one domain assumed to transfer to others
- Credential inflation: treating credentials as proof of correctness
- Milgram effect: deferring to authority even against own judgment
- Inverse authority bias: rejecting claims BECAUSE an authority made them (contrarianism)

When authority IS legitimate evidence:
- The authority is an expert in the specific domain of the claim
- There is consensus among relevant experts
- The claim is within the authority's area of competence
- The authority has a track record of accuracy in this domain

When authority is NOT legitimate evidence:
- The authority is speaking outside their expertise
- The authority has conflicts of interest
- Other equally qualified authorities disagree
- The claim is in a domain where authority doesn't determine truth

Output JSON with: authority_bias_present (bool), severity (none/mild/moderate/severe), authority_cited (who is being cited as authority), authority_domain (what they're actually expert in), claim_domain (what domain the claim is in), domain_match (bool — is the authority relevant?), evidence_independent_of_authority (what evidence exists beyond "X said so"), consensus_among_experts (do other experts agree?), conflict_of_interest (does the authority have incentives?), track_record (how accurate has this authority been?), halo_effect (bool — is expertise being overgeneralized?), credential_vs_competence (are credentials being confused with correctness?), inverse_bias_risk (bool — is contrarian rejection also a risk?), what_would_convince_without_authority (what evidence would be needed if the authority hadn't spoken), recommendation (authority_legitimate/mild_over_deference/significant_authority_bias/authority_irrelevant/evaluate_evidence_directly)."""

AUTHORITY_PROMPT = """Detect authority bias:

Claim: {claim}
Authority cited: {authority}
Authority's domain: {authority_domain}
Evidence beyond authority: {evidence}
Domain: {domain}
Context: {context}

Is authority bias inflating credibility? Return ONLY valid JSON."""


class AuthorityBiasService:
    """Detects authority bias — uncritical acceptance based on source status."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        authority: str = "",
        authority_domain: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect authority bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTHORITY_PROMPT.format(
                claim=claim,
                authority=authority or "Not specified",
                authority_domain=authority_domain or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTHORITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "authority_bias_present": data.get("authority_bias_present", False),
            "severity": data.get("severity", ""),
            "authority_cited": data.get("authority_cited", ""),
            "authority_domain": data.get("authority_domain", ""),
            "claim_domain": data.get("claim_domain", ""),
            "domain_match": data.get("domain_match", False),
            "evidence_independent_of_authority": data.get("evidence_independent_of_authority", ""),
            "consensus_among_experts": data.get("consensus_among_experts", ""),
            "conflict_of_interest": data.get("conflict_of_interest", ""),
            "track_record": data.get("track_record", ""),
            "halo_effect": data.get("halo_effect", False),
            "credential_vs_competence": data.get("credential_vs_competence", ""),
            "inverse_bias_risk": data.get("inverse_bias_risk", False),
            "what_would_convince_without_authority": data.get("what_would_convince_without_authority", ""),
            "recommendation": data.get("recommendation", ""),
        }

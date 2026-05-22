"""CredentialInflationService — Credential Inflation Detection.

Detects credential inflation — treating credentials as stronger
evidence than they are, or inflating what credentials actually
demonstrate about competence or reliability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDENTIAL_INFLATION_SYSTEM = """You are a credential inflation specialist. Given a claim or argument, assess whether credentials are being inflated beyond what they actually demonstrate:

Key concepts:
- Credential inflation: credentials treated as more than they prove
- Degree fetishism: treating degrees as proof of competence
- Certification theater: credentials as performance, not substance
- Credential-competence gap: credentials don't guarantee ability
- Halo of credentials: one credential extending to unrelated areas
- Credentialism: requiring credentials beyond what's needed
- Paper authority: documents substituting for demonstrated ability

When credential inflation IS present:
- Credentials treated as proof of claims they don't support
- Degree or title used to end discussion
- Credentials from one area applied to another
- Formal qualifications equated with actual competence
- Credentials used to dismiss non-credentialed expertise
- What credentials actually certify is inflated
- Credentials substitute for evidence or argument

When credential consideration is appropriate:
- Credentials cited for relevant domain
- Credentials used as one factor among many
- What credentials actually demonstrate is clear
- Credentials reflect genuine training and competence
- Non-credentialed expertise also considered
- Credentials as starting point for trust, not proof
- Limitations of credentials acknowledged

Output JSON with: inflation_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), credentials_cited (what credentials are invoked), actual_scope (what credentials actually demonstrate), inflated_to (what they're being used to prove), recommendation (appropriate_credential_use/mild_inflation/significant_credential_inflation/major_credentialism/evaluate_substance_not_credentials)."""

CREDENTIAL_INFLATION_PROMPT = """Detect credential inflation:

Claim: {claim}
Credentials cited: {credentials}
Relevance: {relevance}
Actual scope: {scope}
Domain: {domain}
Context: {context}

Are credentials being inflated beyond what they actually demonstrate? Return ONLY valid JSON."""


class CredentialInflationService:
    """Detects credential inflation — credentials treated as more than they prove."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        credentials: str = "",
        relevance: str = "",
        scope: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect credential inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDENTIAL_INFLATION_PROMPT.format(
                claim=claim,
                credentials=credentials or "Not specified",
                relevance=relevance or "Not specified",
                scope=scope or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CREDENTIAL_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "inflation_present": data.get("inflation_present", False),
            "severity": data.get("severity", ""),
            "credentials_cited": data.get("credentials_cited", ""),
            "actual_scope": data.get("actual_scope", ""),
            "inflated_to": data.get("inflated_to", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""CredentialParasitismService — Credential Parasitism Detection.

Detects credential parasitism — parasitizing others' credentials
to claim unearned authority or expertise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDENTIAL_PARASITISM_SYSTEM = """You are a credential parasitism specialist. Given a claim of authority, assess whether credentials are being parasitized from others:

Key concepts:
- Credential parasitism: parasitizing others' credentials
- Authority borrowing: borrowing authority without earning it
- Association claims: claiming expertise through association
- Reflected credibility: using others' credibility as one's own
- Institutional parasitism: parasitizing institutional credentials
- Name-dropping authority: using names for unearned authority
- Proximity claims: claiming expertise through proximity

When credential parasitism IS present:
- Others' credentials claimed as one's own
- Authority borrowed without earning
- Association used to claim unearned expertise
- Others' credibility reflected as one's own
- Institutional credentials parasitized
- Names dropped for unearned authority
- Proximity used to claim expertise

When legitimate credential reference is present:
- Own credentials accurately represented
- Authority earned through genuine work
- Association acknowledged honestly
- Credibility built through own contributions
- Institutional affiliation honest
- References made with appropriate context
- Expertise claimed based on genuine work

Output JSON with: parasitism_present (bool), severity (none/mild/moderate/severe), claim (what authority is claimed), source_credentials (whose credentials are parasitized), mechanism (how parasitism works), earned_authority (what authority is actually earned), recommendation (legitimate_reference/mild_overstatement/significant_credential_parasitism/major_authority_theft/earn_own_credentials)."""

CREDENTIAL_PARASITISM_PROMPT = """Detect credential parasitism:

Authority claim: {claim}
Source credentials: {source}
Mechanism: {mechanism}
Earned authority: {earned}
Domain: {domain}
Context: {context}

Are others' credentials being parasitized for unearned authority? Return ONLY valid JSON."""


class CredentialParasitismService:
    """Detects credential parasitism — parasitizing others' credentials."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        source: str = "",
        mechanism: str = "",
        earned: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect credential parasitism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDENTIAL_PARASITISM_PROMPT.format(
                claim=claim,
                source=source or "Not specified",
                mechanism=mechanism or "Not specified",
                earned=earned or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CREDENTIAL_PARASITISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "parasitism_present": data.get("parasitism_present", False),
            "severity": data.get("severity", ""),
            "source_credentials": data.get("source_credentials", ""),
            "mechanism": data.get("mechanism", ""),
            "earned_authority": data.get("earned_authority", ""),
            "recommendation": data.get("recommendation", ""),
        }

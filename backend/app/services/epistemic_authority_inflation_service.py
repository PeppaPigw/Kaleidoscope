"""EpistemicAuthorityInflationService — Epistemic Authority Inflation Detection.

Detects epistemic authority inflation — inflating one's intellectual
authority beyond actual expertise or competence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_INFLATION_SYSTEM = """You are an epistemic authority inflation specialist. Given inflating intellectual authority, assess authority inflation:

Key concepts:
- Epistemic authority inflation: inflating authority beyond actual expertise
- Expertise overclaim: claiming expertise beyond actual knowledge
- Authority expansion: expanding authority claims into unrelated domains
- Credential leveraging: leveraging credentials beyond their scope
- Confidence as authority: using confidence as substitute for authority
- Domain creep: creeping authority claims into new domains
- Unearned authority: claiming authority not earned through genuine expertise

When epistemic authority inflation IS present:
- Inflating authority beyond expertise
- Claiming expertise beyond knowledge
- Expanding authority into unrelated domains
- Leveraging credentials beyond scope
- Using confidence as authority substitute
- Creeping into new domains
- Claiming unearned authority

When no authority inflation:
- Accurate authority claims
- Expertise claims match knowledge
- Authority stays within domain
- Credentials used appropriately
- Confidence matches competence
- Staying within expertise
- Authority genuinely earned

Output JSON with: authority_inflation_detected (bool), severity (none/mild/moderate/severe), expertise_overclaim (what expertise overclaimed), authority_expansion (what domains expanded into), credential_leveraging (what credentials leveraged beyond scope), domain_creep (what domains creeping into), recommendation (no_authority_inflation/mild_accuracy_check/significant_scope_correction/major_intensive_humility_building/emergency_complete_authority_fabrication)."""

EPISTEMIC_AUTHORITY_INFLATION_PROMPT = """Detect epistemic authority inflation:

Expertise overclaim: {expertise_overclaim}
Authority expansion: {authority_expansion}
Credential leveraging: {credential_leveraging}
Domain creep: {domain_creep}
Domain: {domain}
Context: {context}

Is there inflating intellectual authority beyond actual expertise? Return ONLY valid JSON."""


class EpistemicAuthorityInflationService:
    """Detects epistemic authority inflation — inflating authority beyond expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        expertise_overclaim: str,
        *,
        authority_expansion: str = "",
        credential_leveraging: str = "",
        domain_creep: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_INFLATION_PROMPT.format(
                expertise_overclaim=expertise_overclaim,
                authority_expansion=authority_expansion or "Not specified",
                credential_leveraging=credential_leveraging or "Not specified",
                domain_creep=domain_creep or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "expertise_overclaim": expertise_overclaim[:200],
            "authority_inflation_detected": data.get("authority_inflation_detected", False),
            "severity": data.get("severity", ""),
            "authority_expansion": data.get("authority_expansion", ""),
            "credential_leveraging": data.get("credential_leveraging", ""),
            "domain_creep": data.get("domain_creep", ""),
            "recommendation": data.get("recommendation", ""),
        }

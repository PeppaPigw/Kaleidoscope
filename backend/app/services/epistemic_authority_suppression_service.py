"""EpistemicAuthoritySuppressionService — Epistemic Authority Suppression Detection.

Detects epistemic authority suppression — suppressing legitimate authority
through ad hominem attacks, dismissal, or delegitimization.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_SUPPRESSION_SYSTEM = """You are an epistemic authority suppression specialist. Given authority suppression, assess delegitimization:

Key concepts:
- Epistemic authority suppression: suppressing legitimate authority
- Ad hominem delegitimization: attacking person to dismiss expertise
- Credential dismissal: dismissing valid credentials to suppress authority
- Institutional delegitimization: delegitimizing institutions to suppress findings
- Expertise denial: denying expertise exists in a domain
- False democratization: treating all opinions as equally valid regardless of expertise
- Motivated skepticism: applying excessive skepticism to unwanted authorities

When epistemic authority suppression IS present:
- Legitimate authority suppressed
- Ad hominem delegitimization active
- Valid credentials dismissed
- Institutions delegitimized
- Expertise denied
- False democratization imposed
- Motivated skepticism applied

When no authority suppression:
- Authority evaluated fairly
- Credentials assessed on merit
- Institutions evaluated appropriately
- Expertise acknowledged
- Appropriate deference given
- Skepticism calibrated
- Criticism substantive not personal

Output JSON with: authority_suppression_detected (bool), severity (none/mild/moderate/severe), ad_hominem_delegitimization (what ad hominem used), credential_dismissal (what credentials dismissed), institutional_delegitimization (what institutions delegitimized), false_democratization (what false democratization), recommendation (no_authority_suppression/mild_fair_evaluation/significant_expertise_recognition/major_intensive_authority_restoration/emergency_complete_authority_suppression)."""

EPISTEMIC_AUTHORITY_SUPPRESSION_PROMPT = """Detect epistemic authority suppression:

Ad hominem delegitimization: {ad_hominem_delegitimization}
Credential dismissal: {credential_dismissal}
Institutional delegitimization: {institutional_delegitimization}
False democratization: {false_democratization}
Domain: {domain}
Context: {context}

Is legitimate authority being suppressed through delegitimization? Return ONLY valid JSON."""


class EpistemicAuthoritySuppressionService:
    """Detects epistemic authority suppression — delegitimization of expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ad_hominem_delegitimization: str,
        *,
        credential_dismissal: str = "",
        institutional_delegitimization: str = "",
        false_democratization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_SUPPRESSION_PROMPT.format(
                ad_hominem_delegitimization=ad_hominem_delegitimization,
                credential_dismissal=credential_dismissal or "Not specified",
                institutional_delegitimization=institutional_delegitimization or "Not specified",
                false_democratization=false_democratization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ad_hominem_delegitimization": ad_hominem_delegitimization[:200],
            "authority_suppression_detected": data.get("authority_suppression_detected", False),
            "severity": data.get("severity", ""),
            "credential_dismissal": data.get("credential_dismissal", ""),
            "institutional_delegitimization": data.get("institutional_delegitimization", ""),
            "false_democratization": data.get("false_democratization", ""),
            "recommendation": data.get("recommendation", ""),
        }

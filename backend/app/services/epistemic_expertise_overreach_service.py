"""EpistemicExpertiseOverreachService — Epistemic Expertise Overreach Detection.

Detects epistemic expertise overreach — experts applying their expertise
outside their domain where it doesn't validly transfer.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_OVERREACH_SYSTEM = """You are an epistemic expertise overreach specialist. Given experts applying expertise outside their domain, assess overreach:

Key concepts:
- Epistemic expertise overreach: applying expertise outside valid domain
- Domain transfer failure: expertise doesn't transfer to new domain
- Authority inflation: inflating authority beyond competence area
- Halo effect: expertise in one area creating false authority in another
- Confidence transfer: confidence from one domain inappropriately transferred
- Method misapplication: applying domain-specific methods where they don't fit
- Credential overextension: using credentials to claim authority beyond scope

When epistemic expertise overreach IS present:
- Expertise applied outside domain
- Transfer failing
- Authority inflated
- Halo effect operating
- Confidence inappropriately transferred
- Methods misapplied
- Credentials overextended

When no expertise overreach:
- Expertise applied within domain
- Transfer validated
- Authority proportionate
- No halo effect
- Confidence calibrated to domain
- Methods appropriate
- Credentials respected in scope

Output JSON with: expertise_overreach_detected (bool), severity (none/mild/moderate/severe), domain_transfer_failure (what transfer failing), authority_inflation (what authority inflated), method_misapplication (what methods misapplied), credential_overextension (what credentials overextended), recommendation (no_expertise_overreach/mild_domain_awareness/significant_boundary_respect/major_intensive_scope_limiting/emergency_complete_expertise_overreach)."""

EPISTEMIC_EXPERTISE_OVERREACH_PROMPT = """Detect epistemic expertise overreach:

Domain transfer failure: {domain_transfer_failure}
Authority inflation: {authority_inflation}
Method misapplication: {method_misapplication}
Credential overextension: {credential_overextension}
Domain: {domain}
Context: {context}

Is expertise being applied outside its valid domain? Return ONLY valid JSON."""


class EpistemicExpertiseOverreachService:
    """Detects epistemic expertise overreach — expertise beyond valid domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domain_transfer_failure: str,
        *,
        authority_inflation: str = "",
        method_misapplication: str = "",
        credential_overextension: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise overreach."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_OVERREACH_PROMPT.format(
                domain_transfer_failure=domain_transfer_failure,
                authority_inflation=authority_inflation or "Not specified",
                method_misapplication=method_misapplication or "Not specified",
                credential_overextension=credential_overextension or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_OVERREACH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domain_transfer_failure": domain_transfer_failure[:200],
            "expertise_overreach_detected": data.get("expertise_overreach_detected", False),
            "severity": data.get("severity", ""),
            "authority_inflation": data.get("authority_inflation", ""),
            "method_misapplication": data.get("method_misapplication", ""),
            "credential_overextension": data.get("credential_overextension", ""),
            "recommendation": data.get("recommendation", ""),
        }

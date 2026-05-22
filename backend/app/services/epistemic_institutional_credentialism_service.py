"""EpistemicInstitutionalCredentialismService - Credentialism Detection.

Detects credentialism where credentials substitute for argument quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_CREDENTIALISM_SYSTEM = """You are an epistemic institutional credentialism specialist. Given credential-based claims, assess whether credentials substitute for argument quality:

Key concepts:
- Credentialism: treating credentials as proof of correctness rather than indicators of training
- Argument displacement: credentials used instead of evidence or reasoning
- Expertise conflation: assuming expertise in one domain transfers to another
- Outsider dismissal: rejecting valid arguments from non-credentialed sources

When credentialism IS present:
- Credentials used as argument
- Evidence displaced by authority
- Cross-domain expertise assumed
- Non-credentialed voices dismissed
- Quality of reasoning ignored

When no credentialism:
- Credentials contextualize but don't replace argument
- Evidence evaluated on merits
- Domain boundaries respected
- Arguments assessed regardless of source
- Reasoning quality prioritized

Output JSON with: credentialism_detected (bool), severity (none/mild/moderate/severe), argument_displacement (what argument displaced), expertise_conflation (what expertise conflated), outsider_dismissal (what outsider dismissed), recommendation (no_credentialism/mild_merit_check/significant_argument_restoration/major_evidence_reconstruction/emergency_complete_credentialism)."""

EPISTEMIC_INSTITUTIONAL_CREDENTIALISM_PROMPT = """Detect epistemic institutional credentialism:

Credential claim: {credential_claim}
Argument displacement: {argument_displacement}
Expertise conflation: {expertise_conflation}
Outsider dismissal: {outsider_dismissal}
Domain: {domain}
Context: {context}

Are credentials substituting for argument quality? Return ONLY valid JSON."""


class EpistemicInstitutionalCredentialismService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        credential_claim: str,
        *,
        argument_displacement: str = "",
        expertise_conflation: str = "",
        outsider_dismissal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_CREDENTIALISM_PROMPT.format(
                credential_claim=credential_claim,
                argument_displacement=argument_displacement or "Not specified",
                expertise_conflation=expertise_conflation or "Not specified",
                outsider_dismissal=outsider_dismissal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_CREDENTIALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "credential_claim": credential_claim[:200],
            "credentialism_detected": data.get("credentialism_detected", False),
            "severity": data.get("severity", ""),
            "argument_displacement": data.get("argument_displacement", ""),
            "expertise_conflation": data.get("expertise_conflation", ""),
            "outsider_dismissal": data.get("outsider_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }

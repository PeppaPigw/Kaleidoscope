"""EpistemicExpertiseCredentialismService — Epistemic Expertise Credentialism Detection.

Detects epistemic expertise credentialism — evaluating claims based on credentials
rather than evidence quality, conflating institutional status with correctness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_CREDENTIALISM_SYSTEM = """You are an epistemic expertise credentialism specialist. Given credentialist reasoning, assess credential-over-evidence distortion:

Key concepts:
- Epistemic credentialism: credentials substituting for evidence evaluation
- Degree worship: treating degrees as proof of correctness
- Institutional prestige: prestigious institution implying correct claims
- Publication count: quantity of publications implying quality of claims
- Title authority: job titles substituting for argument quality
- Credential gatekeeping: dismissing claims from non-credentialed sources
- Reverse credentialism: dismissing claims because source has wrong credentials

When epistemic credentialism IS present:
- Credentials substituting for evidence
- Degrees treated as proof
- Prestige implying correctness
- Publication count as quality proxy
- Titles substituting for arguments
- Non-credentialed dismissed
- Wrong credentials used to dismiss

When no credentialism:
- Evidence evaluated independently
- Degrees contextualized
- Prestige not conflated with correctness
- Publication quality assessed
- Arguments evaluated on merit
- All sources considered
- Claims evaluated regardless of source

Output JSON with: credentialism_detected (bool), severity (none/mild/moderate/severe), degree_worship (what degrees treated as proof), institutional_prestige (what prestige implying correctness), credential_gatekeeping (what non-credentialed dismissed), reverse_credentialism (what wrong credentials dismissing), recommendation (no_credentialism/mild_evidence_focus/significant_merit_evaluation/major_intensive_source_independence/emergency_complete_credentialism)."""

EPISTEMIC_EXPERTISE_CREDENTIALISM_PROMPT = """Detect epistemic expertise credentialism:

Degree worship: {degree_worship}
Institutional prestige: {institutional_prestige}
Credential gatekeeping: {credential_gatekeeping}
Reverse credentialism: {reverse_credentialism}
Domain: {domain}
Context: {context}

Are credentials being used to evaluate claims instead of evidence? Return ONLY valid JSON."""


class EpistemicExpertiseCredentialismService:
    """Detects epistemic expertise credentialism — credentials over evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        degree_worship: str,
        *,
        institutional_prestige: str = "",
        credential_gatekeeping: str = "",
        reverse_credentialism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise credentialism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_CREDENTIALISM_PROMPT.format(
                degree_worship=degree_worship,
                institutional_prestige=institutional_prestige or "Not specified",
                credential_gatekeeping=credential_gatekeeping or "Not specified",
                reverse_credentialism=reverse_credentialism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_CREDENTIALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "degree_worship": degree_worship[:200],
            "credentialism_detected": data.get("credentialism_detected", False),
            "severity": data.get("severity", ""),
            "institutional_prestige": data.get("institutional_prestige", ""),
            "credential_gatekeeping": data.get("credential_gatekeeping", ""),
            "reverse_credentialism": data.get("reverse_credentialism", ""),
            "recommendation": data.get("recommendation", ""),
        }

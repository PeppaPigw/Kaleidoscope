"""CredentialOverArgumentService — Credential Over Argument Detection.

Detects credential-over-argument — substituting credentials,
qualifications, or status for actual arguments, where the person's
title or degree is treated as sufficient reason to accept a claim.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDENTIAL_OVER_ARGUMENT_SYSTEM = """You are a credential-over-argument specialist. Given a discourse, assess whether credentials are substituting for arguments:

Key concepts:
- Credential substitution: credentials replacing reasoning
- Title as argument: degree or position as sufficient reason
- Status over substance: social status over logical merit
- Qualification gatekeeping: only credentialed views count
- Argument from CV: career history as evidence
- Degree fetishism: formal education as proof of correctness
- Position authority: job title as argument

When credential-over-argument IS present:
- Credentials cited instead of providing reasoning
- Title or degree treated as sufficient justification
- Status used to dismiss need for argument
- Only credentialed views given consideration
- Career history substitutes for evidence
- Formal qualifications treated as proof
- Position used to end rather than inform discussion

When credential citation is appropriate:
- Credentials establish relevant expertise context
- Qualifications supplement rather than replace argument
- Status acknowledged but reasoning still provided
- Credentials used to weight, not determine, conclusions
- Experience cited alongside substantive reasoning
- Qualifications indicate relevant background knowledge
- Position provides context for perspective offered

Output JSON with: substitution_present (bool), severity (none/mild/moderate/severe), discourse (what is being discussed), credential_cited (what credential is invoked), argument_missing (what argument is absent), reasoning_needed (what reasoning would be appropriate), recommendation (appropriate_credential_context/mild_credential_reliance/significant_credential_substitution/major_argument_absence/provide_reasoning_with_credentials)."""

CREDENTIAL_OVER_ARGUMENT_PROMPT = """Detect credential-over-argument:

Discourse: {discourse}
Credential cited: {credential}
Argument provided: {argument}
Reasoning quality: {reasoning}
Domain: {domain}
Context: {context}

Are credentials being substituted for actual arguments? Return ONLY valid JSON."""


class CredentialOverArgumentService:
    """Detects credential-over-argument — credentials replacing reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        credential: str = "",
        argument: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect credential-over-argument."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDENTIAL_OVER_ARGUMENT_PROMPT.format(
                discourse=discourse,
                credential=credential or "Not specified",
                argument=argument or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CREDENTIAL_OVER_ARGUMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "substitution_present": data.get("substitution_present", False),
            "severity": data.get("severity", ""),
            "credential_cited": data.get("credential_cited", ""),
            "argument_missing": data.get("argument_missing", ""),
            "reasoning_needed": data.get("reasoning_needed", ""),
            "recommendation": data.get("recommendation", ""),
        }

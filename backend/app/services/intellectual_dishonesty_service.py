"""IntellectualDishonestyService — Intellectual Dishonesty Detection.

Detects intellectual dishonesty — knowingly misrepresenting evidence
or arguments, where the speaker knows their representation is
inaccurate but presents it anyway.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_DISHONESTY_SYSTEM = """You are an intellectual dishonesty specialist. Given a representation of evidence or arguments, assess whether knowing misrepresentation is occurring:

Key concepts:
- Intellectual dishonesty: knowingly misrepresenting evidence
- Deliberate distortion: intentional misrepresentation
- Evidence misrepresentation: presenting evidence inaccurately
- Argument distortion: misrepresenting others' arguments
- Knowing omission: deliberately omitting relevant information
- Strategic misquoting: quoting out of context deliberately
- Bad faith representation: representing in bad faith

When intellectual dishonesty IS present:
- Evidence knowingly misrepresented
- Arguments deliberately distorted
- Relevant information intentionally omitted
- Quotes taken out of context deliberately
- Representation known to be inaccurate
- Distortion serving rhetorical rather than truth goals
- Bad faith in representing evidence or positions

When honest disagreement is present:
- Representation good faith even if imperfect
- Disagreement about interpretation not representation
- Omissions due to relevance judgment not strategy
- Quotes in appropriate context
- Representation genuinely believed accurate
- Disagreement serving understanding
- Good faith in representing opposing views

Output JSON with: dishonesty_present (bool), severity (none/mild/moderate/severe), representation (what is represented), distortion (how it is distorted), known_accuracy (what accurate version would be), motivation (why distortion occurs), recommendation (honest_representation/mild_inaccuracy/significant_intellectual_dishonesty/major_deliberate_distortion/represent_evidence_accurately)."""

INTELLECTUAL_DISHONESTY_PROMPT = """Detect intellectual dishonesty:

Representation: {representation}
Actual evidence: {actual}
Distortion: {distortion}
Context: {disc_context}
Domain: {domain}
Context: {context}

Is evidence or argument being knowingly misrepresented? Return ONLY valid JSON."""


class IntellectualDishonestyService:
    """Detects intellectual dishonesty — knowingly misrepresenting evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        representation: str,
        *,
        actual: str = "",
        distortion: str = "",
        disc_context: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual dishonesty."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_DISHONESTY_PROMPT.format(
                representation=representation,
                actual=actual or "Not specified",
                distortion=distortion or "Not specified",
                disc_context=disc_context or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_DISHONESTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "representation": representation[:200],
            "dishonesty_present": data.get("dishonesty_present", False),
            "severity": data.get("severity", ""),
            "distortion": data.get("distortion", ""),
            "known_accuracy": data.get("known_accuracy", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }

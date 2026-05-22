"""PrivatePublicConfusionService — Private-Public Epistemic Confusion Detection.

Detects private-public epistemic confusion — confusing private
epistemic standards with public ones, where personal conviction
is treated as public evidence or public standards are imposed on
private belief.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRIVATE_PUBLIC_CONFUSION_SYSTEM = """You are a private-public epistemic confusion specialist. Given a claim, assess whether private and public epistemic standards are being confused:

Key concepts:
- Private-public confusion: mixing personal and public standards
- Personal conviction as public evidence: private certainty as proof
- Public standards on private belief: imposing public rigor on personal
- Testimony confusion: personal experience as universal evidence
- Subjective-objective conflation: treating subjective as objective
- Anecdote as data: personal experience as general evidence
- Private certainty as public warrant: feeling sure as proving

When private-public confusion IS present:
- Personal conviction treated as public evidence
- Private certainty presented as objective proof
- Personal experience generalized without justification
- Subjective standards applied to public claims
- Anecdotal evidence treated as systematic
- Private epistemic standards confused with public ones
- Feeling certain treated as being right

When distinction is maintained:
- Personal and public evidence distinguished
- Private conviction acknowledged as personal
- Experience shared without over-generalizing
- Subjective and objective clearly separated
- Anecdotes contextualized appropriately
- Different standards for private and public claims
- Certainty distinguished from correctness

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), private_standard (what private standard is used), public_standard (what public standard applies), conflation (how they are confused), recommendation (appropriate_distinction/mild_boundary_blur/significant_private_public_confusion/major_standard_conflation/maintain_private_public_distinction)."""

PRIVATE_PUBLIC_CONFUSION_PROMPT = """Detect private-public epistemic confusion:

Claim: {claim}
Evidence type: {evidence_type}
Standard applied: {standard}
Audience: {audience}
Domain: {domain}
Context: {context}

Are private and public epistemic standards being confused? Return ONLY valid JSON."""


class PrivatePublicConfusionService:
    """Detects private-public epistemic confusion — mixing personal and public standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence_type: str = "",
        standard: str = "",
        audience: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect private-public epistemic confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRIVATE_PUBLIC_CONFUSION_PROMPT.format(
                claim=claim,
                evidence_type=evidence_type or "Not specified",
                standard=standard or "Not specified",
                audience=audience or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRIVATE_PUBLIC_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "confusion_present": data.get("confusion_present", False),
            "severity": data.get("severity", ""),
            "private_standard": data.get("private_standard", ""),
            "public_standard": data.get("public_standard", ""),
            "conflation": data.get("conflation", ""),
            "recommendation": data.get("recommendation", ""),
        }

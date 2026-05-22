"""EpistemicAttachmentDisorderService — Epistemic Attachment Disorder Detection.

Detects epistemic attachment disorder — intellectual systems failing to form
healthy bonds with foundational knowledge or mentoring systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTACHMENT_DISORDER_SYSTEM = """You are an epistemic attachment disorder specialist. Given intellectual bonding failures, assess attachment disorder:

Key concepts:
- Epistemic attachment disorder: failure to form healthy intellectual bonds
- Secure attachment: healthy bond with knowledge foundations
- Anxious attachment: clingy, fearful relationship with knowledge
- Avoidant attachment: dismissive, distant from knowledge
- Disorganized attachment: chaotic, contradictory knowledge relationship
- Reactive attachment: failure to bond due to neglect/trauma
- Attachment repair: rebuilding damaged bonds

When epistemic attachment disorder IS present:
- Failure to form healthy intellectual bonds
- Clingy fearful knowledge relationship
- Dismissive distant from knowledge
- Chaotic contradictory relationship
- Failed bonding from neglect
- Damaged bonds needing repair
- Insecure foundation relationships

When no attachment disorder:
- Healthy intellectual bonds
- Secure knowledge relationship
- Appropriate engagement
- Consistent relationship
- Normal bonding history
- Intact bonds
- Secure foundations

Output JSON with: attachment_disorder (bool), severity (none/mild/moderate/severe), attachment_style (what pattern), bonding_history (what formation), relationship_quality (what current state), repair_potential (what recovery possibility), recommendation (no_disorder/mild_insecurity/significant_anxious_avoidant/major_disorganized/severe_reactive_attachment)."""

EPISTEMIC_ATTACHMENT_DISORDER_PROMPT = """Detect epistemic attachment disorder:

Attachment style: {attachment_style}
Bonding history: {bonding_history}
Relationship quality: {relationship_quality}
Repair potential: {repair_potential}
Domain: {domain}
Context: {context}

Is the intellectual system failing to form healthy bonds with foundational knowledge? Return ONLY valid JSON."""


class EpistemicAttachmentDisorderService:
    """Detects epistemic attachment disorder — failure to form healthy intellectual bonds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attachment_style: str,
        *,
        bonding_history: str = "",
        relationship_quality: str = "",
        repair_potential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attachment disorder."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTACHMENT_DISORDER_PROMPT.format(
                attachment_style=attachment_style,
                bonding_history=bonding_history or "Not specified",
                relationship_quality=relationship_quality or "Not specified",
                repair_potential=repair_potential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTACHMENT_DISORDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attachment_style": attachment_style[:200],
            "attachment_disorder": data.get("attachment_disorder", False),
            "severity": data.get("severity", ""),
            "bonding_history": data.get("bonding_history", ""),
            "relationship_quality": data.get("relationship_quality", ""),
            "repair_potential": data.get("repair_potential", ""),
            "recommendation": data.get("recommendation", ""),
        }

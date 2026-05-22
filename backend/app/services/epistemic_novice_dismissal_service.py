"""EpistemicNoviceDismissalService — Epistemic Novice Dismissal Detection.

Detects epistemic novice dismissal — dismissing insights because they
come from non-experts rather than evaluating them on merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NOVICE_DISMISSAL_SYSTEM = """You are an epistemic novice dismissal specialist. Given dismissal of insights from non-experts, assess novice dismissal:

Key concepts:
- Epistemic novice dismissal: dismissing insights because source is non-expert
- Source over content: evaluating by source rather than content
- Credential gatekeeping: requiring credentials to be heard
- Fresh eyes blindness: missing value of fresh perspective
- Beginner's mind rejection: rejecting beginner's mind insights
- Status hierarchy: using status to dismiss rather than engage
- Expertise elitism: elitist attitude toward non-expert contributions

When epistemic novice dismissal IS present:
- Insights dismissed due to source
- Source evaluated over content
- Credentials required to be heard
- Fresh perspective missed
- Beginner's mind rejected
- Status used to dismiss
- Elitism toward non-experts

When no novice dismissal:
- Insights evaluated on merit
- Content over source
- Ideas heard regardless of credentials
- Fresh perspective valued
- Beginner's mind welcomed
- Status not used to dismiss
- Inclusive toward all contributors

Output JSON with: novice_dismissal_detected (bool), severity (none/mild/moderate/severe), source_over_content (what dismissed by source), credential_gatekeeping (what credentials required), fresh_eyes_blindness (what fresh perspective missed), status_hierarchy (what status used to dismiss), recommendation (no_novice_dismissal/mild_merit_evaluation/significant_inclusion_practice/major_intensive_elitism_correction/emergency_complete_novice_dismissal)."""

EPISTEMIC_NOVICE_DISMISSAL_PROMPT = """Detect epistemic novice dismissal:

Source over content: {source_over_content}
Credential gatekeeping: {credential_gatekeeping}
Fresh eyes blindness: {fresh_eyes_blindness}
Status hierarchy: {status_hierarchy}
Domain: {domain}
Context: {context}

Are insights being dismissed because they come from non-experts? Return ONLY valid JSON."""


class EpistemicNoviceDismissalService:
    """Detects epistemic novice dismissal — source over content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source_over_content: str,
        *,
        credential_gatekeeping: str = "",
        fresh_eyes_blindness: str = "",
        status_hierarchy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic novice dismissal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NOVICE_DISMISSAL_PROMPT.format(
                source_over_content=source_over_content,
                credential_gatekeeping=credential_gatekeeping or "Not specified",
                fresh_eyes_blindness=fresh_eyes_blindness or "Not specified",
                status_hierarchy=status_hierarchy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NOVICE_DISMISSAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source_over_content": source_over_content[:200],
            "novice_dismissal_detected": data.get("novice_dismissal_detected", False),
            "severity": data.get("severity", ""),
            "credential_gatekeeping": data.get("credential_gatekeeping", ""),
            "fresh_eyes_blindness": data.get("fresh_eyes_blindness", ""),
            "status_hierarchy": data.get("status_hierarchy", ""),
            "recommendation": data.get("recommendation", ""),
        }

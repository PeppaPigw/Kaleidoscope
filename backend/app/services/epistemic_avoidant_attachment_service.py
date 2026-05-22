"""EpistemicAvoidantAttachmentService — Epistemic Avoidant Attachment Detection.

Detects epistemic avoidant attachment — dismissive avoidance of intellectual
intimacy and deep engagement with others' ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AVOIDANT_ATTACHMENT_SYSTEM = """You are an epistemic avoidant attachment specialist. Given dismissive avoidance of intellectual intimacy, assess attachment:

Key concepts:
- Epistemic avoidant attachment: dismissing intellectual closeness
- Deactivation: suppressing need for intellectual connection
- Self-sufficiency compulsion: insisting on intellectual independence
- Intimacy avoidance: keeping intellectual relationships shallow
- Dismissiveness: minimizing importance of intellectual others
- Pseudo-independence: appearing not to need intellectual support
- Distancing: creating space when closeness threatens

When epistemic avoidant attachment IS present:
- Dismissing intellectual closeness
- Suppressing connection need
- Insisting on independence
- Keeping relationships shallow
- Minimizing others' importance
- Appearing not to need
- Creating distance

When no avoidant attachment:
- Comfortable with closeness
- Acknowledging connection needs
- Interdependent
- Deep relationships
- Valuing others
- Accepting support
- Comfortable proximity

Output JSON with: avoidant_attachment_detected (bool), severity (none/mild/moderate/severe), deactivation_pattern (what suppressing), self_sufficiency_compulsion (what insisting), intimacy_avoidance (what keeping shallow), distancing_behavior (what creating space), recommendation (no_avoidant_attachment/mild_connection_practice/significant_attachment_therapy/major_intensive_restructuring/emergency_severe_avoidance)."""

EPISTEMIC_AVOIDANT_ATTACHMENT_PROMPT = """Detect epistemic avoidant attachment:

Deactivation pattern: {deactivation_pattern}
Self sufficiency compulsion: {self_sufficiency_compulsion}
Intimacy avoidance: {intimacy_avoidance}
Distancing behavior: {distancing_behavior}
Domain: {domain}
Context: {context}

Is there dismissive avoidance of intellectual intimacy and deep engagement? Return ONLY valid JSON."""


class EpistemicAvoidantAttachmentService:
    """Detects epistemic avoidant attachment — dismissing intellectual closeness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deactivation_pattern: str,
        *,
        self_sufficiency_compulsion: str = "",
        intimacy_avoidance: str = "",
        distancing_behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic avoidant attachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AVOIDANT_ATTACHMENT_PROMPT.format(
                deactivation_pattern=deactivation_pattern,
                self_sufficiency_compulsion=self_sufficiency_compulsion or "Not specified",
                intimacy_avoidance=intimacy_avoidance or "Not specified",
                distancing_behavior=distancing_behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AVOIDANT_ATTACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deactivation_pattern": deactivation_pattern[:200],
            "avoidant_attachment_detected": data.get("avoidant_attachment_detected", False),
            "severity": data.get("severity", ""),
            "self_sufficiency_compulsion": data.get("self_sufficiency_compulsion", ""),
            "intimacy_avoidance": data.get("intimacy_avoidance", ""),
            "distancing_behavior": data.get("distancing_behavior", ""),
            "recommendation": data.get("recommendation", ""),
        }

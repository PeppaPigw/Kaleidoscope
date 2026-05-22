"""EpistemicReactiveAttachmentService — Epistemic Reactive Attachment Detection.

Detects epistemic reactive attachment — disrupted intellectual bonding
patterns from early intellectual neglect or inconsistent mentoring.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REACTIVE_ATTACHMENT_SYSTEM = """You are an epistemic reactive attachment specialist. Given disrupted intellectual bonding, assess reactive attachment:

Key concepts:
- Epistemic reactive attachment: disrupted intellectual bonding
- Inhibited: emotionally withdrawn from intellectual relationships
- Disinhibited: indiscriminate intellectual attachment
- Neglect history: early intellectual deprivation
- Trust deficit: inability to trust intellectual mentors
- Comfort seeking: not turning to others for intellectual support
- Social reciprocity: impaired intellectual give-and-take

When epistemic reactive attachment IS present:
- Disrupted intellectual bonding
- Withdrawn from relationships
- Indiscriminate attachment
- Early intellectual deprivation
- Cannot trust mentors
- Not seeking support
- Impaired give-and-take

When no reactive attachment:
- Healthy intellectual bonding
- Engaged in relationships
- Selective appropriate attachment
- Adequate intellectual nurturing
- Trusting mentors
- Seeking support when needed
- Normal reciprocity

Output JSON with: reactive_attachment_detected (bool), severity (none/mild/moderate/severe), attachment_pattern (what disruption), trust_capacity (what deficit), neglect_history (what deprivation), reciprocity_level (what give-and-take), recommendation (no_reactive_attachment/mild_relationship_building/significant_attachment_therapy/major_intensive_treatment/emergency_complete_isolation)."""

EPISTEMIC_REACTIVE_ATTACHMENT_PROMPT = """Detect epistemic reactive attachment:

Attachment pattern: {attachment_pattern}
Trust capacity: {trust_capacity}
Neglect history: {neglect_history}
Reciprocity level: {reciprocity_level}
Domain: {domain}
Context: {context}

Is there disrupted intellectual bonding from early neglect or inconsistent mentoring? Return ONLY valid JSON."""


class EpistemicReactiveAttachmentService:
    """Detects epistemic reactive attachment — disrupted intellectual bonding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attachment_pattern: str,
        *,
        trust_capacity: str = "",
        neglect_history: str = "",
        reciprocity_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reactive attachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REACTIVE_ATTACHMENT_PROMPT.format(
                attachment_pattern=attachment_pattern,
                trust_capacity=trust_capacity or "Not specified",
                neglect_history=neglect_history or "Not specified",
                reciprocity_level=reciprocity_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REACTIVE_ATTACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attachment_pattern": attachment_pattern[:200],
            "reactive_attachment_detected": data.get("reactive_attachment_detected", False),
            "severity": data.get("severity", ""),
            "trust_capacity": data.get("trust_capacity", ""),
            "neglect_history": data.get("neglect_history", ""),
            "reciprocity_level": data.get("reciprocity_level", ""),
            "recommendation": data.get("recommendation", ""),
        }

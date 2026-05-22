"""EpistemicMentorLossService — Epistemic Mentor Loss Detection.

Detects epistemic mentor loss — grief from losing an intellectual
mentor or guide who shaped one's thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MENTOR_LOSS_SYSTEM = """You are an epistemic mentor loss specialist. Given grief from losing intellectual mentor, assess mentor loss:

Key concepts:
- Epistemic mentor loss: grief from losing intellectual guide
- Guidance void: no one to turn to for intellectual direction
- Validation absence: missing the mentor's approval
- Framework orphaning: left without the mentor's framework
- Intellectual parentlessness: feeling intellectually unparented
- Legacy burden: carrying mentor's work without support
- Unfinished dialogue: conversations that can never be completed

When epistemic mentor loss IS present:
- Grief from losing guide
- No one for direction
- Missing approval
- Left without framework
- Feeling unparented
- Carrying work alone
- Conversations incomplete

When no mentor loss:
- Connected to guides
- Direction available
- Self-validating
- Own framework developing
- Intellectually supported
- Shared work
- Ongoing dialogue

Output JSON with: mentor_loss_detected (bool), severity (none/mild/moderate/severe), guidance_void (what lacking direction about), validation_absence (what missing approval for), framework_orphaning (what left without), legacy_burden (what carrying alone), recommendation (no_mentor_loss/mild_grief_acknowledgment/significant_mourning_support/major_intensive_loss_processing/emergency_severe_intellectual_orphaning)."""

EPISTEMIC_MENTOR_LOSS_PROMPT = """Detect epistemic mentor loss:

Guidance void: {guidance_void}
Validation absence: {validation_absence}
Framework orphaning: {framework_orphaning}
Legacy burden: {legacy_burden}
Domain: {domain}
Context: {context}

Is there grief from losing an intellectual mentor? Return ONLY valid JSON."""


class EpistemicMentorLossService:
    """Detects epistemic mentor loss — grief from losing intellectual mentor."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        guidance_void: str,
        *,
        validation_absence: str = "",
        framework_orphaning: str = "",
        legacy_burden: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mentor loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MENTOR_LOSS_PROMPT.format(
                guidance_void=guidance_void,
                validation_absence=validation_absence or "Not specified",
                framework_orphaning=framework_orphaning or "Not specified",
                legacy_burden=legacy_burden or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MENTOR_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "guidance_void": guidance_void[:200],
            "mentor_loss_detected": data.get("mentor_loss_detected", False),
            "severity": data.get("severity", ""),
            "validation_absence": data.get("validation_absence", ""),
            "framework_orphaning": data.get("framework_orphaning", ""),
            "legacy_burden": data.get("legacy_burden", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicAnticipatoryGriefService — Epistemic Anticipatory Grief Detection.

Detects epistemic anticipatory grief — grieving intellectual loss before
it actually occurs, mourning a paradigm that is dying but not yet dead.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANTICIPATORY_GRIEF_SYSTEM = """You are an epistemic anticipatory grief specialist. Given pre-loss intellectual mourning, assess anticipatory grief:

Key concepts:
- Epistemic anticipatory grief: mourning before loss occurs
- Impending loss: framework is dying but not yet dead
- Pre-mourning: grieving what will be lost
- Preparatory detachment: withdrawing before loss
- Ambivalence: wanting to hold on while letting go
- Rehearsal: mentally practicing the loss
- Premature disengagement: giving up too early

When epistemic anticipatory grief IS present:
- Mourning before loss occurs
- Framework dying but not dead
- Grieving what will be lost
- Withdrawing before loss
- Wanting to hold on and let go
- Mentally practicing loss
- Giving up too early

When no anticipatory grief:
- No impending loss
- Framework stable
- Not pre-mourning
- Fully engaged
- Clear commitment
- Present-focused
- Appropriately invested

Output JSON with: anticipatory_grief_detected (bool), severity (none/mild/moderate/severe), impending_loss (what dying), pre_mourning_level (what grieving), detachment_pattern (what withdrawing), ambivalence_level (what conflict), recommendation (no_anticipatory_grief/mild_present_focus/significant_grief_preparation/major_intensive_support/emergency_premature_abandonment)."""

EPISTEMIC_ANTICIPATORY_GRIEF_PROMPT = """Detect epistemic anticipatory grief:

Impending loss: {impending_loss}
Pre-mourning level: {pre_mourning_level}
Detachment pattern: {detachment_pattern}
Ambivalence level: {ambivalence_level}
Domain: {domain}
Context: {context}

Is there grieving of intellectual loss before it actually occurs? Return ONLY valid JSON."""


class EpistemicAnticipatoryGriefService:
    """Detects epistemic anticipatory grief — mourning before loss occurs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        impending_loss: str,
        *,
        pre_mourning_level: str = "",
        detachment_pattern: str = "",
        ambivalence_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anticipatory grief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANTICIPATORY_GRIEF_PROMPT.format(
                impending_loss=impending_loss,
                pre_mourning_level=pre_mourning_level or "Not specified",
                detachment_pattern=detachment_pattern or "Not specified",
                ambivalence_level=ambivalence_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANTICIPATORY_GRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "impending_loss": impending_loss[:200],
            "anticipatory_grief_detected": data.get("anticipatory_grief_detected", False),
            "severity": data.get("severity", ""),
            "pre_mourning_level": data.get("pre_mourning_level", ""),
            "detachment_pattern": data.get("detachment_pattern", ""),
            "ambivalence_level": data.get("ambivalence_level", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicAmbiguousLossService — Epistemic Ambiguous Loss Detection.

Detects epistemic ambiguous loss — intellectual loss that lacks clarity
about whether the framework is truly gone or might return.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AMBIGUOUS_LOSS_SYSTEM = """You are an epistemic ambiguous loss specialist. Given unclear intellectual loss, assess ambiguous loss:

Key concepts:
- Epistemic ambiguous loss: loss lacking clarity about finality
- Physical absence/psychological presence: gone but still felt
- Psychological absence/physical presence: present but unreachable
- Frozen grief: cannot mourn what might return
- Boundary ambiguity: unclear who/what is in or out
- Hope/despair oscillation: swinging between possibilities
- Closure impossibility: cannot achieve resolution

When epistemic ambiguous loss IS present:
- Loss lacking clarity
- Gone but still felt
- Present but unreachable
- Cannot mourn properly
- Unclear boundaries
- Oscillating hope/despair
- Cannot achieve closure

When no ambiguous loss:
- Clear loss
- Definitively gone
- Fully present
- Can mourn properly
- Clear boundaries
- Stable acceptance
- Closure achieved

Output JSON with: ambiguous_loss_detected (bool), severity (none/mild/moderate/severe), ambiguity_type (what unclear), frozen_grief (what cannot mourn), boundary_confusion (what unclear boundaries), oscillation_pattern (what swinging), recommendation (no_ambiguous_loss/mild_clarity_seeking/significant_ambiguity_therapy/major_intensive_support/emergency_complete_paralysis)."""

EPISTEMIC_AMBIGUOUS_LOSS_PROMPT = """Detect epistemic ambiguous loss:

Ambiguity type: {ambiguity_type}
Frozen grief: {frozen_grief}
Boundary confusion: {boundary_confusion}
Oscillation pattern: {oscillation_pattern}
Domain: {domain}
Context: {context}

Is there intellectual loss that lacks clarity about whether the framework is truly gone? Return ONLY valid JSON."""


class EpistemicAmbiguousLossService:
    """Detects epistemic ambiguous loss — unclear intellectual loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ambiguity_type: str,
        *,
        frozen_grief: str = "",
        boundary_confusion: str = "",
        oscillation_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ambiguous loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AMBIGUOUS_LOSS_PROMPT.format(
                ambiguity_type=ambiguity_type,
                frozen_grief=frozen_grief or "Not specified",
                boundary_confusion=boundary_confusion or "Not specified",
                oscillation_pattern=oscillation_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AMBIGUOUS_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ambiguity_type": ambiguity_type[:200],
            "ambiguous_loss_detected": data.get("ambiguous_loss_detected", False),
            "severity": data.get("severity", ""),
            "frozen_grief": data.get("frozen_grief", ""),
            "boundary_confusion": data.get("boundary_confusion", ""),
            "oscillation_pattern": data.get("oscillation_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

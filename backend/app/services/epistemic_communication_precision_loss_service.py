"""EpistemicCommunicationPrecisionLossService — Epistemic Communication Precision Loss Detection.

Detects epistemic communication precision loss — loss of precision through
communication, nuance stripped in transmission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_PRECISION_LOSS_SYSTEM = """You are an epistemic communication precision loss specialist. Given precision lost in communication, assess precision loss:

Key concepts:
- Epistemic communication precision loss: nuance stripped in transmission
- Qualifier dropping: dropping qualifiers and hedges in retelling
- Confidence inflation: tentative claims becoming certain through retelling
- Boundary erosion: precise boundaries becoming vague
- Conditional loss: conditional statements becoming unconditional
- Range collapse: ranges collapsing to point estimates
- Exception erasure: exceptions being erased in communication

When epistemic communication precision loss IS present:
- Precision lost in transmission
- Qualifiers dropped
- Confidence inflated
- Boundaries eroded
- Conditionals lost
- Ranges collapsed
- Exceptions erased

When no precision loss:
- Precision maintained
- Qualifiers preserved
- Confidence calibrated
- Boundaries maintained
- Conditionals preserved
- Ranges maintained
- Exceptions noted

Output JSON with: precision_loss_detected (bool), severity (none/mild/moderate/severe), qualifier_dropping (what qualifiers dropped), confidence_inflation (what confidence inflated), boundary_erosion (what boundaries eroded), conditional_loss (what conditionals lost), recommendation (no_precision_loss/mild_qualifier_preservation/significant_precision_recovery/major_intensive_nuance_restoration/emergency_complete_precision_loss)."""

EPISTEMIC_COMMUNICATION_PRECISION_LOSS_PROMPT = """Detect epistemic communication precision loss:

Qualifier dropping: {qualifier_dropping}
Confidence inflation: {confidence_inflation}
Boundary erosion: {boundary_erosion}
Conditional loss: {conditional_loss}
Domain: {domain}
Context: {context}

Is precision being lost through communication, with nuance stripped? Return ONLY valid JSON."""


class EpistemicCommunicationPrecisionLossService:
    """Detects epistemic communication precision loss — nuance stripped."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        qualifier_dropping: str,
        *,
        confidence_inflation: str = "",
        boundary_erosion: str = "",
        conditional_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication precision loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_PRECISION_LOSS_PROMPT.format(
                qualifier_dropping=qualifier_dropping,
                confidence_inflation=confidence_inflation or "Not specified",
                boundary_erosion=boundary_erosion or "Not specified",
                conditional_loss=conditional_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_PRECISION_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "qualifier_dropping": qualifier_dropping[:200],
            "precision_loss_detected": data.get("precision_loss_detected", False),
            "severity": data.get("severity", ""),
            "confidence_inflation": data.get("confidence_inflation", ""),
            "boundary_erosion": data.get("boundary_erosion", ""),
            "conditional_loss": data.get("conditional_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }

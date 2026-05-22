"""EpistemicFeedbackInhibitionService — Epistemic Feedback Inhibition Detection.

Detects epistemic feedback inhibition — intellectual output suppressing
its own production signal, creating self-limiting thought patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEEDBACK_INHIBITION_SYSTEM = """You are an epistemic feedback inhibition specialist. Given an intellectual production system, assess whether output suppresses its own production:

Key concepts:
- Epistemic feedback inhibition: output suppressing its own production signal
- Negative feedback: product inhibiting its own synthesis
- End-product inhibition: final product shutting down pathway
- Allosteric regulation: product changing enzyme shape to reduce activity
- Homeostatic setpoint: target level that triggers inhibition
- Gain control: adjusting sensitivity of inhibition
- Escape from inhibition: overriding the suppression

When epistemic feedback inhibition IS present:
- Intellectual output suppressing its own production
- Products inhibiting their own synthesis
- Final conclusions shutting down further inquiry
- Ideas changing the intellectual machinery to reduce output
- Target levels triggering suppression of further thought
- Sensitivity of inhibition being adjusted
- Attempts to override the self-suppression

When no inhibition is present:
- No self-suppression of output
- No product inhibition
- No pathway shutdown
- No allosteric regulation
- No homeostatic setpoint
- No gain control
- No need for escape

Output JSON with: feedback_inhibition_present (bool), severity (none/mild/moderate/severe), negative_feedback (what product inhibition), end_product_inhibition (what pathway shutdown), allosteric_regulation (what shape change), homeostatic_setpoint (what target level), recommendation (no_inhibition/mild_inhibition/significant_feedback_inhibition/major_self_suppression/release_inhibition)."""

EPISTEMIC_FEEDBACK_INHIBITION_PROMPT = """Detect epistemic feedback inhibition:

Negative feedback: {negative_feedback}
End-product inhibition: {end_product_inhibition}
Allosteric regulation: {allosteric_regulation}
Homeostatic setpoint: {homeostatic_setpoint}
Domain: {domain}
Context: {context}

Is intellectual output suppressing its own production signal, creating self-limiting patterns? Return ONLY valid JSON."""


class EpistemicFeedbackInhibitionService:
    """Detects epistemic feedback inhibition — output suppressing its own production."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        negative_feedback: str,
        *,
        end_product_inhibition: str = "",
        allosteric_regulation: str = "",
        homeostatic_setpoint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic feedback inhibition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEEDBACK_INHIBITION_PROMPT.format(
                negative_feedback=negative_feedback,
                end_product_inhibition=end_product_inhibition or "Not specified",
                allosteric_regulation=allosteric_regulation or "Not specified",
                homeostatic_setpoint=homeostatic_setpoint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEEDBACK_INHIBITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "negative_feedback": negative_feedback[:200],
            "feedback_inhibition_present": data.get("feedback_inhibition_present", False),
            "severity": data.get("severity", ""),
            "end_product_inhibition": data.get("end_product_inhibition", ""),
            "allosteric_regulation": data.get("allosteric_regulation", ""),
            "homeostatic_setpoint": data.get("homeostatic_setpoint", ""),
            "recommendation": data.get("recommendation", ""),
        }

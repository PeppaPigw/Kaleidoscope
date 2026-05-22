"""EpistemicNegativeFeedbackSuppressionService — Epistemic Negative Feedback Suppression Detection.

Detects epistemic negative feedback suppression — suppressing corrective
feedback that would fix errors in thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NEGATIVE_FEEDBACK_SUPPRESSION_SYSTEM = """You are an epistemic negative feedback suppression specialist. Given suppression of corrective feedback, assess feedback suppression:

Key concepts:
- Epistemic negative feedback suppression: suppressing corrective feedback
- Correction avoidance: avoiding information that would correct errors
- Critic silencing: silencing critics who provide corrective feedback
- Warning dismissal: dismissing warnings and red flags
- Error signal blocking: blocking signals that indicate errors
- Disconfirmation resistance: resisting disconfirming evidence
- Homeostasis disruption: disrupting natural error-correction mechanisms

When epistemic negative feedback suppression IS present:
- Corrective feedback suppressed
- Corrections avoided
- Critics silenced
- Warnings dismissed
- Error signals blocked
- Disconfirmation resisted
- Error-correction disrupted

When no negative feedback suppression:
- Corrective feedback welcomed
- Corrections sought
- Critics heard
- Warnings heeded
- Error signals attended to
- Disconfirmation processed
- Error-correction functioning

Output JSON with: negative_feedback_suppression_detected (bool), severity (none/mild/moderate/severe), correction_avoidance (what corrections avoided), critic_silencing (what critics silenced), warning_dismissal (what warnings dismissed), error_signal_blocking (what signals blocked), recommendation (no_feedback_suppression/mild_openness_practice/significant_correction_welcoming/major_intensive_feedback_restoration/emergency_complete_feedback_suppression)."""

EPISTEMIC_NEGATIVE_FEEDBACK_SUPPRESSION_PROMPT = """Detect epistemic negative feedback suppression:

Correction avoidance: {correction_avoidance}
Critic silencing: {critic_silencing}
Warning dismissal: {warning_dismissal}
Error signal blocking: {error_signal_blocking}
Domain: {domain}
Context: {context}

Is corrective feedback being suppressed? Return ONLY valid JSON."""


class EpistemicNegativeFeedbackSuppressionService:
    """Detects epistemic negative feedback suppression — correction blocked."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        correction_avoidance: str,
        *,
        critic_silencing: str = "",
        warning_dismissal: str = "",
        error_signal_blocking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic negative feedback suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NEGATIVE_FEEDBACK_SUPPRESSION_PROMPT.format(
                correction_avoidance=correction_avoidance,
                critic_silencing=critic_silencing or "Not specified",
                warning_dismissal=warning_dismissal or "Not specified",
                error_signal_blocking=error_signal_blocking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NEGATIVE_FEEDBACK_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "correction_avoidance": correction_avoidance[:200],
            "negative_feedback_suppression_detected": data.get("negative_feedback_suppression_detected", False),
            "severity": data.get("severity", ""),
            "critic_silencing": data.get("critic_silencing", ""),
            "warning_dismissal": data.get("warning_dismissal", ""),
            "error_signal_blocking": data.get("error_signal_blocking", ""),
            "recommendation": data.get("recommendation", ""),
        }

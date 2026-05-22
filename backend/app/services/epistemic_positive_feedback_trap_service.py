"""EpistemicPositiveFeedbackTrapService — Epistemic Positive Feedback Trap Detection.

Detects epistemic positive feedback trap — positive feedback loops
amplifying errors rather than correcting them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POSITIVE_FEEDBACK_TRAP_SYSTEM = """You are an epistemic positive feedback trap specialist. Given positive feedback loops amplifying errors, assess feedback trap:

Key concepts:
- Epistemic positive feedback trap: positive feedback amplifying errors
- Error amplification: errors getting amplified through feedback
- Confirmation spiral: confirming beliefs creating more confirmation
- Echo chamber dynamics: feedback reinforcing without correction
- Runaway belief: beliefs running away from evidence
- Self-fulfilling prophecy: belief creating evidence for itself
- Escalation dynamics: each step making correction harder

When epistemic positive feedback trap IS present:
- Positive feedback amplifying errors
- Errors getting larger
- Confirmation spiraling
- Echo chamber operating
- Beliefs running away
- Self-fulfilling prophecies active
- Escalation making correction harder

When no positive feedback trap:
- Feedback corrective
- Errors dampened
- Confirmation checked
- Multiple perspectives present
- Beliefs anchored to evidence
- Prophecies tested
- Correction possible at any point

Output JSON with: positive_feedback_trap_detected (bool), severity (none/mild/moderate/severe), error_amplification (what errors amplified), confirmation_spiral (what spiraling), echo_chamber_dynamics (what echo chamber), runaway_belief (what running away), recommendation (no_positive_feedback_trap/mild_dampening_practice/significant_correction_introduction/major_intensive_loop_breaking/emergency_complete_positive_feedback_trap)."""

EPISTEMIC_POSITIVE_FEEDBACK_TRAP_PROMPT = """Detect epistemic positive feedback trap:

Error amplification: {error_amplification}
Confirmation spiral: {confirmation_spiral}
Echo chamber dynamics: {echo_chamber_dynamics}
Runaway belief: {runaway_belief}
Domain: {domain}
Context: {context}

Are positive feedback loops amplifying errors? Return ONLY valid JSON."""


class EpistemicPositiveFeedbackTrapService:
    """Detects epistemic positive feedback trap — error amplification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        error_amplification: str,
        *,
        confirmation_spiral: str = "",
        echo_chamber_dynamics: str = "",
        runaway_belief: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic positive feedback trap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POSITIVE_FEEDBACK_TRAP_PROMPT.format(
                error_amplification=error_amplification,
                confirmation_spiral=confirmation_spiral or "Not specified",
                echo_chamber_dynamics=echo_chamber_dynamics or "Not specified",
                runaway_belief=runaway_belief or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POSITIVE_FEEDBACK_TRAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "error_amplification": error_amplification[:200],
            "positive_feedback_trap_detected": data.get("positive_feedback_trap_detected", False),
            "severity": data.get("severity", ""),
            "confirmation_spiral": data.get("confirmation_spiral", ""),
            "echo_chamber_dynamics": data.get("echo_chamber_dynamics", ""),
            "runaway_belief": data.get("runaway_belief", ""),
            "recommendation": data.get("recommendation", ""),
        }

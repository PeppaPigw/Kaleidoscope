"""EpistemicDelayedFeedbackService — Epistemic Delayed Feedback Detection.

Detects epistemic delayed feedback — feedback arriving too late
to enable timely correction of errors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DELAYED_FEEDBACK_SYSTEM = """You are an epistemic delayed feedback specialist. Given feedback arriving too late for correction, assess delayed feedback:

Key concepts:
- Epistemic delayed feedback: feedback too late for timely correction
- Temporal gap: gap between action and feedback too large
- Correction window missed: window for correction has passed
- Accumulated error: errors accumulating before feedback arrives
- Attribution difficulty: delay making it hard to attribute cause
- Learning impairment: delay impairing learning from mistakes
- Intervention timing: interventions too late to be effective

When epistemic delayed feedback IS present:
- Feedback arriving too late
- Temporal gap too large
- Correction window missed
- Errors accumulating
- Attribution difficult
- Learning impaired
- Interventions too late

When no delayed feedback:
- Feedback timely
- Temporal gap appropriate
- Correction window open
- Errors caught early
- Attribution clear
- Learning enabled
- Interventions timely

Output JSON with: delayed_feedback_detected (bool), severity (none/mild/moderate/severe), temporal_gap (what gap too large), correction_window_missed (what window missed), accumulated_error (what errors accumulated), attribution_difficulty (what attribution difficult), recommendation (no_delayed_feedback/mild_feedback_acceleration/significant_monitoring_improvement/major_intensive_real_time_feedback/emergency_complete_delayed_feedback)."""

EPISTEMIC_DELAYED_FEEDBACK_PROMPT = """Detect epistemic delayed feedback:

Temporal gap: {temporal_gap}
Correction window missed: {correction_window_missed}
Accumulated error: {accumulated_error}
Attribution difficulty: {attribution_difficulty}
Domain: {domain}
Context: {context}

Is feedback arriving too late for timely correction? Return ONLY valid JSON."""


class EpistemicDelayedFeedbackService:
    """Detects epistemic delayed feedback — correction too late."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        temporal_gap: str,
        *,
        correction_window_missed: str = "",
        accumulated_error: str = "",
        attribution_difficulty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic delayed feedback."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DELAYED_FEEDBACK_PROMPT.format(
                temporal_gap=temporal_gap,
                correction_window_missed=correction_window_missed or "Not specified",
                accumulated_error=accumulated_error or "Not specified",
                attribution_difficulty=attribution_difficulty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DELAYED_FEEDBACK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "temporal_gap": temporal_gap[:200],
            "delayed_feedback_detected": data.get("delayed_feedback_detected", False),
            "severity": data.get("severity", ""),
            "correction_window_missed": data.get("correction_window_missed", ""),
            "accumulated_error": data.get("accumulated_error", ""),
            "attribution_difficulty": data.get("attribution_difficulty", ""),
            "recommendation": data.get("recommendation", ""),
        }

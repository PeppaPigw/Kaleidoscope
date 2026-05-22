"""EpistemicFeedbackAvoidanceService — Epistemic Feedback Avoidance Detection.

Detects epistemic feedback avoidance — actively avoiding feedback
to protect existing beliefs from challenge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEEDBACK_AVOIDANCE_SYSTEM = """You are an epistemic feedback avoidance specialist. Given active avoidance of feedback, assess feedback avoidance:

Key concepts:
- Epistemic feedback avoidance: actively avoiding feedback to protect beliefs
- Information avoidance: avoiding information that might challenge beliefs
- Testing avoidance: avoiding tests that might reveal errors
- Evaluation resistance: resisting evaluation of one's work or thinking
- Accountability evasion: evading accountability for epistemic claims
- Measurement avoidance: avoiding measurement that might disconfirm
- Outcome tracking avoidance: avoiding tracking outcomes of predictions

When epistemic feedback avoidance IS present:
- Feedback actively avoided
- Information avoided
- Tests avoided
- Evaluation resisted
- Accountability evaded
- Measurement avoided
- Outcomes not tracked

When no feedback avoidance:
- Feedback sought
- Information welcomed
- Tests embraced
- Evaluation accepted
- Accountability embraced
- Measurement welcomed
- Outcomes tracked

Output JSON with: feedback_avoidance_detected (bool), severity (none/mild/moderate/severe), information_avoidance (what information avoided), testing_avoidance (what tests avoided), evaluation_resistance (what evaluation resisted), accountability_evasion (what accountability evaded), recommendation (no_feedback_avoidance/mild_openness_practice/significant_feedback_seeking/major_intensive_accountability_building/emergency_complete_feedback_avoidance)."""

EPISTEMIC_FEEDBACK_AVOIDANCE_PROMPT = """Detect epistemic feedback avoidance:

Information avoidance: {information_avoidance}
Testing avoidance: {testing_avoidance}
Evaluation resistance: {evaluation_resistance}
Accountability evasion: {accountability_evasion}
Domain: {domain}
Context: {context}

Is feedback being actively avoided to protect beliefs? Return ONLY valid JSON."""


class EpistemicFeedbackAvoidanceService:
    """Detects epistemic feedback avoidance — protecting beliefs from challenge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_avoidance: str,
        *,
        testing_avoidance: str = "",
        evaluation_resistance: str = "",
        accountability_evasion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic feedback avoidance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEEDBACK_AVOIDANCE_PROMPT.format(
                information_avoidance=information_avoidance,
                testing_avoidance=testing_avoidance or "Not specified",
                evaluation_resistance=evaluation_resistance or "Not specified",
                accountability_evasion=accountability_evasion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEEDBACK_AVOIDANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_avoidance": information_avoidance[:200],
            "feedback_avoidance_detected": data.get("feedback_avoidance_detected", False),
            "severity": data.get("severity", ""),
            "testing_avoidance": data.get("testing_avoidance", ""),
            "evaluation_resistance": data.get("evaluation_resistance", ""),
            "accountability_evasion": data.get("accountability_evasion", ""),
            "recommendation": data.get("recommendation", ""),
        }

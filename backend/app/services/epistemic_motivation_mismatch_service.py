"""EpistemicMotivationMismatchService — Epistemic Motivation Mismatch Detection.

Detects epistemic motivation mismatch — motivation misaligned with
epistemic goals, pursuing wrong things for wrong reasons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOTIVATION_MISMATCH_SYSTEM = """You are an epistemic motivation mismatch specialist. Given motivation misaligned with epistemic goals, assess motivation mismatch:

Key concepts:
- Epistemic motivation mismatch: motivation misaligned with epistemic goals
- Goal misalignment: pursuing goals that don't serve understanding
- Means-end confusion: confusing means of knowing with ends
- Status over truth: motivated by status rather than truth
- Performance over learning: motivated by performance not learning
- Approval over accuracy: motivated by approval not accuracy
- Completion over comprehension: motivated to finish not understand

When epistemic motivation mismatch IS present:
- Motivation misaligned with goals
- Goals not serving understanding
- Means confused with ends
- Status prioritized over truth
- Performance over learning
- Approval over accuracy
- Completion over comprehension

When no motivation mismatch:
- Motivation aligned with goals
- Goals serving understanding
- Means and ends clear
- Truth prioritized
- Learning prioritized
- Accuracy prioritized
- Comprehension prioritized

Output JSON with: motivation_mismatch_detected (bool), severity (none/mild/moderate/severe), goal_misalignment (what goals misaligned), status_over_truth (what status prioritized over truth), performance_over_learning (what performance over learning), completion_over_comprehension (what completion over comprehension), recommendation (no_motivation_mismatch/mild_realignment_practice/significant_goal_correction/major_intensive_motivation_restructuring/emergency_complete_motivation_mismatch)."""

EPISTEMIC_MOTIVATION_MISMATCH_PROMPT = """Detect epistemic motivation mismatch:

Goal misalignment: {goal_misalignment}
Status over truth: {status_over_truth}
Performance over learning: {performance_over_learning}
Completion over comprehension: {completion_over_comprehension}
Domain: {domain}
Context: {context}

Is motivation misaligned with epistemic goals? Return ONLY valid JSON."""


class EpistemicMotivationMismatchService:
    """Detects epistemic motivation mismatch — motivation misaligned with goals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        goal_misalignment: str,
        *,
        status_over_truth: str = "",
        performance_over_learning: str = "",
        completion_over_comprehension: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic motivation mismatch."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOTIVATION_MISMATCH_PROMPT.format(
                goal_misalignment=goal_misalignment,
                status_over_truth=status_over_truth or "Not specified",
                performance_over_learning=performance_over_learning or "Not specified",
                completion_over_comprehension=completion_over_comprehension or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOTIVATION_MISMATCH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "goal_misalignment": goal_misalignment[:200],
            "motivation_mismatch_detected": data.get("motivation_mismatch_detected", False),
            "severity": data.get("severity", ""),
            "status_over_truth": data.get("status_over_truth", ""),
            "performance_over_learning": data.get("performance_over_learning", ""),
            "completion_over_comprehension": data.get("completion_over_comprehension", ""),
            "recommendation": data.get("recommendation", ""),
        }

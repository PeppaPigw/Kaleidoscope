"""LessonOverfittingService — Lesson Overfitting Detection.

Detects lesson overfitting — over-learning from a single past experience
and applying its lessons too broadly, where one data point becomes
an overgeneralized rule.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LESSON_OVERFITTING_SYSTEM = """You are a lesson overfitting specialist. Given a lesson being applied, assess whether it is overfitted to a single past experience:

Key concepts:
- Lesson overfitting: over-learning from one experience
- Single-case generalization: one event becoming universal rule
- Trauma-driven rules: painful experience creating rigid rules
- Success formula fixation: one success becoming the only approach
- Context blindness: ignoring how new context differs from original
- Pattern matching failure: seeing the old pattern everywhere
- Overgeneralized heuristic: narrow lesson applied too broadly

When lesson overfitting IS present:
- Single experience generating broad rules
- Lesson applied without regard to context differences
- One success/failure becoming universal template
- New situations forced into old pattern
- Context differences between original and current ignored
- Rigid application of narrow lesson
- Inability to see when lesson doesn't apply

When learning from experience is appropriate:
- Lessons proportionate to evidence base
- Context similarities and differences noted
- Multiple experiences informing the lesson
- Lesson bounded to appropriate scope
- New contexts evaluated on their own terms
- Flexibility in applying past learning
- Recognition of when lessons don't transfer

Output JSON with: overfitting_present (bool), severity (none/mild/moderate/severe), lesson (what lesson is applied), source_experience (what experience generated it), current_context (where it's being applied), context_mismatch (how contexts differ), recommendation (appropriate_learning/mild_overgeneralization/significant_lesson_overfitting/major_single_case_fixation/bound_lesson_to_appropriate_scope)."""

LESSON_OVERFITTING_PROMPT = """Detect lesson overfitting:

Lesson applied: {lesson}
Source experience: {source}
Current context: {current}
Context differences: {differences}
Domain: {domain}
Context: {context}

Is a lesson from limited experience being applied too broadly? Return ONLY valid JSON."""


class LessonOverfittingService:
    """Detects lesson overfitting — over-learning from single experiences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        lesson: str,
        *,
        source: str = "",
        current: str = "",
        differences: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect lesson overfitting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LESSON_OVERFITTING_PROMPT.format(
                lesson=lesson,
                source=source or "Not specified",
                current=current or "Not specified",
                differences=differences or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LESSON_OVERFITTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "lesson": lesson[:200],
            "overfitting_present": data.get("overfitting_present", False),
            "severity": data.get("severity", ""),
            "source_experience": data.get("source_experience", ""),
            "current_context": data.get("current_context", ""),
            "context_mismatch": data.get("context_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }

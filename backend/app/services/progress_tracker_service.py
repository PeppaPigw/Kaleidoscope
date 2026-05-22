"""ProgressTrackerService — Research Question Resolution Progress.

Takes a research question and findings so far, assesses how much
progress has been made toward answering it. Identifies what's resolved,
what remains open, and what the next highest-value investigation would be.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROGRESS_SYSTEM = """You are a research progress assessment specialist. Given a question and findings so far, assess:
- What fraction of the question is answered (0-1)
- Which sub-questions are resolved vs open
- Whether the findings so far change the original question
- What the highest-value next step would be
- Whether we're approaching diminishing returns

Output JSON with: resolution_score (0-1, how much of the question is answered), resolved_aspects (list of what's been answered), open_aspects (list of what remains), question_evolved (bool, has the question changed based on findings), evolved_question (if yes, what's the new question), next_highest_value (single most valuable next investigation), diminishing_returns (bool, are we past the point of easy gains), confidence_in_current_answer (0-1), blockers (what's preventing further progress), estimated_effort_remaining (low/moderate/high/enormous)."""

PROGRESS_PROMPT = """Assess research progress:

Original question: {question}
Findings so far:
{findings}

Domain: {domain}

How much progress have we made? Return ONLY valid JSON."""


class ProgressTrackerService:
    """Tracks progress toward answering research questions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_progress(
        self,
        question: str,
        findings: list[str],
        *,
        domain: str = "",
    ) -> dict:
        """Assess progress toward answering a research question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        findings_formatted = "\n".join(f"- {f}" for f in findings[:10])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROGRESS_PROMPT.format(
                question=question,
                findings=findings_formatted,
                domain=domain or "general",
            ),
            system=PROGRESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "question": question[:200],
            "resolution_score": data.get("resolution_score", 0),
            "resolved_aspects": data.get("resolved_aspects", []),
            "open_aspects": data.get("open_aspects", []),
            "question_evolved": data.get("question_evolved", False),
            "evolved_question": data.get("evolved_question", ""),
            "next_highest_value": data.get("next_highest_value", ""),
            "diminishing_returns": data.get("diminishing_returns", False),
            "confidence_in_current_answer": data.get("confidence_in_current_answer", 0),
            "blockers": data.get("blockers", []),
            "estimated_effort_remaining": data.get("estimated_effort_remaining", ""),
        }

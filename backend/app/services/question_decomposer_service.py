"""QuestionDecomposerService — Research Question Decomposition.

Breaks complex research questions into tractable sub-questions with
dependency ordering. Identifies which sub-questions must be answered
first, which can be parallelized, and which are the crux questions
that determine the overall answer.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECOMPOSE_SYSTEM = """You are a research question decomposition specialist. Given a complex research question, break it into tractable sub-questions. For each sub-question identify:
- Is it answerable with current methods?
- What does it depend on (which other sub-questions must be answered first)?
- How much does answering it reduce overall uncertainty?
- Is it a crux question (one whose answer determines the overall conclusion)?

Output JSON with: decomposition.original_question, decomposition.sub_questions (list of: id (q1, q2...), question, answerable (bool), method (how to answer it), dependencies (list of ids), uncertainty_reduction (0-1), is_crux (bool), estimated_difficulty (easy/moderate/hard/very_hard)), decomposition.dependency_order (list of ids in optimal answering order), decomposition.parallelizable_groups (list of groups that can be investigated simultaneously), decomposition.crux_questions (which sub-questions are most decisive), decomposition.estimated_total_effort (low/moderate/high/very_high)."""

DECOMPOSE_PROMPT = """Decompose this research question:

Question: {question}
Domain: {domain}
Constraints: {constraints}

Break into tractable sub-questions with dependencies. Return ONLY valid JSON."""


class QuestionDecomposerService:
    """Decomposes complex research questions into tractable sub-questions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def decompose(
        self,
        question: str,
        *,
        domain: str = "",
        constraints: str = "",
    ) -> dict:
        """Decompose a complex question into sub-questions."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECOMPOSE_PROMPT.format(
                question=question,
                domain=domain or "research",
                constraints=constraints or "No specific constraints",
            ),
            system=DECOMPOSE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        decomp = data.get("decomposition", data)

        sub_questions = decomp.get("sub_questions", [])
        return {
            "question": question[:200],
            "sub_question_count": len(sub_questions),
            "sub_questions": sub_questions,
            "dependency_order": decomp.get("dependency_order", []),
            "parallelizable_groups": decomp.get("parallelizable_groups", []),
            "crux_questions": decomp.get("crux_questions", []),
            "total_effort": decomp.get("estimated_total_effort", ""),
        }

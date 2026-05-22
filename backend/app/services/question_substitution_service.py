"""QuestionSubstitutionService — Question Substitution Detection.

Detects question substitution — when a difficult question is
unconsciously replaced with an easier one. The answer to the
easier question is then presented as if it answers the original
harder question.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

QUESTION_SUBSTITUTION_SYSTEM = """You are a question substitution specialist. Given a question and answer, assess whether the actual question was substituted with an easier one:

Key concepts:
- Question substitution: replacing hard question with easier one
- Attribute substitution: judging one attribute by substituting another
- Heuristic answering: using mental shortcuts instead of careful analysis
- Target attribute: what was actually asked about
- Heuristic attribute: what was actually answered
- Affect heuristic: substituting "how do I feel?" for "what do I think?"
- Availability substitution: "how easily can I recall?" for "how frequent?"

When question substitution IS present:
- Answer addresses a different (easier) question than asked
- Complex question answered with simple heuristic
- "How likely?" answered with "how easily can I imagine it?"
- "How good?" answered with "how do I feel about it?"
- "What's the probability?" answered with "does it fit the pattern?"
- Quantitative question answered qualitatively
- Specific question answered with general platitude

When question substitution is NOT present:
- Answer directly addresses the question asked
- Complexity of answer matches complexity of question
- Hard questions acknowledged as hard
- Appropriate analytical methods used for the question type
- Distinction maintained between what was asked and what's easy to answer
- Heuristics used consciously with awareness of limitations
- Answer would satisfy someone who asked the original question

Output JSON with: substitution_present (bool), severity (none/mild/moderate/severe), original_question (what was actually asked), substituted_question (what was actually answered), difficulty_gap (how much easier the substitute is), heuristic_used (what shortcut was employed), recommendation (no_substitution/mild_simplification/significant_substitution/major_question_dodge/answer_actual_question)."""

QUESTION_SUBSTITUTION_PROMPT = """Detect question substitution:

Original question: {question}
Answer given: {answer}
Method used: {method}
Complexity: {complexity}
Domain: {domain}
Context: {context}

Was the actual question substituted with an easier one? Return ONLY valid JSON."""


class QuestionSubstitutionService:
    """Detects question substitution — answering easier questions instead."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        question: str,
        *,
        answer: str = "",
        method: str = "",
        complexity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect question substitution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=QUESTION_SUBSTITUTION_PROMPT.format(
                question=question,
                answer=answer or "Not specified",
                method=method or "Not specified",
                complexity=complexity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=QUESTION_SUBSTITUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "question": question[:200],
            "substitution_present": data.get("substitution_present", False),
            "severity": data.get("severity", ""),
            "original_question": data.get("original_question", ""),
            "substituted_question": data.get("substituted_question", ""),
            "heuristic_used": data.get("heuristic_used", ""),
            "recommendation": data.get("recommendation", ""),
        }

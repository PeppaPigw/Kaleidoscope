"""LoadedQuestionService — Loaded Question Detection.

Detects loaded question — asking a question that contains an
unproven assumption or presupposition, making it impossible to
answer without appearing to accept the embedded premise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LOADED_QUESTION_SYSTEM = """You are a loaded question specialist. Given a question, assess whether it contains unproven presuppositions:

Key concepts:
- Loaded question: question containing an unproven assumption
- Presupposition: what must be true for the question to make sense
- Complex question: combining multiple questions into one
- Leading question: question that suggests its own answer
- Embedded claim: assertion hidden within a question
- "Have you stopped...?": classic loaded question form
- Legitimate presupposition: some assumptions are established facts

When loaded question IS present:
- "Why did you steal the money?" (presupposes theft occurred)
- "Have you stopped beating your wife?" (presupposes past abuse)
- "When will you admit you were wrong?" (presupposes being wrong)
- Questions that can't be answered yes/no without accepting a premise
- "Why is X so terrible?" (presupposes X is terrible)
- Embedding contested claims as if they were established
- Questions designed to trap the respondent

When loaded question is NOT present:
- The presupposition is an established fact
- The question is genuinely seeking information
- Any assumptions are explicitly stated and open to challenge
- The question can be answered without accepting contested premises
- Leading questions in appropriate contexts (rhetoric, not deception)
- The presupposition has been previously established in the conversation
- The question is complex but not deceptively so

Output JSON with: loaded_question_present (bool), severity (none/mild/moderate/severe), question (the question asked), presupposition (what is assumed), established (is the presupposition established), trap (how answering accepts the premise), recommendation (no_loaded_question/mild_assumption/significant_loaded_question/major_presupposition_trap/challenge_the_premise)."""

LOADED_QUESTION_PROMPT = """Detect loaded question:

Question: {question}
Presupposition: {presupposition}
Established facts: {established}
Answering options: {options}
Domain: {domain}
Context: {context}

Does this question contain unproven presuppositions that trap the respondent? Return ONLY valid JSON."""


class LoadedQuestionService:
    """Detects loaded question — questions with unproven presuppositions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        question: str,
        *,
        presupposition: str = "",
        established: str = "",
        options: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect loaded question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LOADED_QUESTION_PROMPT.format(
                question=question,
                presupposition=presupposition or "Not specified",
                established=established or "Not specified",
                options=options or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LOADED_QUESTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "question": question[:200],
            "loaded_question_present": data.get("loaded_question_present", False),
            "severity": data.get("severity", ""),
            "presupposition": data.get("presupposition", ""),
            "established": data.get("established", ""),
            "trap": data.get("trap", ""),
            "recommendation": data.get("recommendation", ""),
        }

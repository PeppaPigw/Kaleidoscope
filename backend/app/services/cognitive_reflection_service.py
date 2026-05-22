"""CognitiveReflectionService — Cognitive Reflection Failure Detection.

Detects cognitive reflection failures — situations where intuitive
(System 1) answers are accepted without engaging deliberative
(System 2) thinking. Frederick (2005). The bat-and-ball problem
illustrates: most people answer "10 cents" because the intuitive
answer feels right and they don't check it analytically.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COGNITIVE_REFLECTION_SYSTEM = """You are a cognitive reflection specialist. Given a reasoning situation, assess whether intuitive answers are being accepted without deliberative verification:

Key concepts (Frederick, 2005):
- Cognitive reflection: ability to override intuitive wrong answers
- System 1 trap: problems designed to trigger wrong intuitions
- Miserly processing: accepting first answer without checking
- Attribute substitution: answering easier question instead
- Feeling of rightness: intuitive confidence without verification
- Cognitive laziness: not engaging effortful thinking
- Base rate neglect: ignoring statistical information for narratives

When cognitive reflection failure IS present:
- Accepting the first answer that comes to mind without checking
- High confidence in answers to tricky questions
- Not noticing when a problem has a non-obvious structure
- Substituting an easier question for the actual question
- Ignoring mathematical or logical structure
- "Obviously it's X" for problems that aren't obvious
- Not double-checking intuitive answers against constraints

When intuitive answers ARE appropriate:
- The problem genuinely is straightforward
- Domain expertise makes intuition reliable
- Time pressure justifies heuristic answers
- The stakes don't warrant deliberative effort
- The person has verified their intuition is calibrated
- Pattern recognition from extensive experience

Output JSON with: cognitive_reflection_failure (bool), severity (none/mild/moderate/severe), problem (what is being reasoned about), intuitive_answer (what intuition suggests), analytical_answer (what deliberation reveals), trap_type (what makes this problem tricky), verification_attempted (was the answer checked), confidence_calibration (is confidence appropriate), recommendation (reflection_adequate/mild_intuition_reliance/significant_reflection_failure/major_system1_dominance/engage_deliberative_thinking)."""

COGNITIVE_REFLECTION_PROMPT = """Detect cognitive reflection failure:

Situation: {situation}
Reasoning: {reasoning}
Answer given: {answer}
Verification: {verification}
Domain: {domain}
Context: {context}

Is an intuitive answer being accepted without deliberative verification? Return ONLY valid JSON."""


class CognitiveReflectionService:
    """Detects cognitive reflection failures — intuition without verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        reasoning: str = "",
        answer: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cognitive reflection failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COGNITIVE_REFLECTION_PROMPT.format(
                situation=situation,
                reasoning=reasoning or "Not specified",
                answer=answer or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COGNITIVE_REFLECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "cognitive_reflection_failure": data.get("cognitive_reflection_failure", False),
            "severity": data.get("severity", ""),
            "intuitive_answer": data.get("intuitive_answer", ""),
            "analytical_answer": data.get("analytical_answer", ""),
            "trap_type": data.get("trap_type", ""),
            "verification_attempted": data.get("verification_attempted", ""),
            "confidence_calibration": data.get("confidence_calibration", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""QuestionBeggingFramingService — Question-Begging Framing Detection.

Detects question-begging framing — framing a situation in terms
that presuppose the conclusion, where the way the question is posed
already contains the answer being argued for.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

QUESTION_BEGGING_FRAMING_SYSTEM = """You are a question-begging framing specialist. Given a framing, assess whether it presupposes its own conclusion:

Key concepts:
- Question-begging framing: framing that presupposes conclusion
- Loaded framing: terms that contain the answer
- Presuppositional language: language that assumes what's argued
- Circular framing: frame and conclusion are the same
- Embedded assumptions: conclusions hidden in premises
- Leading framing: framing that leads to predetermined answer
- Definitional smuggling: definitions that contain conclusions

When question-begging framing IS present:
- Framing presupposes the conclusion being argued
- Terms used already contain the answer
- Language assumes what needs to be demonstrated
- Frame and conclusion are circular
- Conclusions embedded in how question is posed
- Framing leads inevitably to predetermined answer
- Definitions smuggle in what should be argued

When framing is appropriate:
- Terms defined independently of conclusion
- Framing allows multiple conclusions
- Assumptions made explicit and arguable
- Language neutral between competing answers
- Definitions don't predetermine outcome
- Frame can be questioned without rejecting conclusion
- Multiple framings considered

Output JSON with: begging_present (bool), severity (none/mild/moderate/severe), framing (what framing is used), presupposition (what is presupposed), conclusion (what conclusion is predetermined), alternative_framing (what neutral framing would look like), recommendation (appropriate_framing/mild_leading_language/significant_question_begging/major_presuppositional_framing/use_neutral_framing)."""

QUESTION_BEGGING_FRAMING_PROMPT = """Detect question-begging framing:

Framing: {framing}
Conclusion argued: {conclusion}
Terms used: {terms}
Alternative framing: {alternative}
Domain: {domain}
Context: {context}

Does this framing presuppose its own conclusion? Return ONLY valid JSON."""


class QuestionBeggingFramingService:
    """Detects question-begging framing — framing that presupposes conclusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        framing: str,
        *,
        conclusion: str = "",
        terms: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect question-begging framing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=QUESTION_BEGGING_FRAMING_PROMPT.format(
                framing=framing,
                conclusion=conclusion or "Not specified",
                terms=terms or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=QUESTION_BEGGING_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "framing": framing[:200],
            "begging_present": data.get("begging_present", False),
            "severity": data.get("severity", ""),
            "presupposition": data.get("presupposition", ""),
            "conclusion": data.get("conclusion", ""),
            "alternative_framing": data.get("alternative_framing", ""),
            "recommendation": data.get("recommendation", ""),
        }

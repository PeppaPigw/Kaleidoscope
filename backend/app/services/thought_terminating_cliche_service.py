"""ThoughtTerminatingClicheService — Thought-Terminating Cliche Detection.

Detects thought-terminating cliches — stock phrases used to end
critical thinking and shut down further inquiry. These phrases
sound wise but actually prevent deeper analysis by providing
a false sense of resolution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

THOUGHT_TERMINATING_SYSTEM = """You are a thought-terminating cliche specialist. Given a statement or response, assess whether it uses stock phrases to shut down critical thinking:

Key concepts:
- Thought-terminating cliche: phrase that ends inquiry
- Semantic stop sign: words that halt further analysis
- Cached thought: pre-packaged response that prevents thinking
- Deepity: statement that sounds profound but is trivially true or meaninglessly vague
- Bumper sticker wisdom: oversimplified slogans masquerading as insight
- Conversation stopper: phrases designed to end discussion
- False resolution: creating a sense of closure without actual understanding

When thought-terminating cliche IS present:
- "It is what it is" (prevents asking why or how to change it)
- "Everything happens for a reason" (prevents causal analysis)
- "That's just how things are" (prevents questioning the status quo)
- "You can't fight city hall" (prevents considering action)
- "It's just common sense" (prevents examining assumptions)
- "God works in mysterious ways" (prevents seeking explanation)
- "There are two sides to every story" (prevents evaluating evidence)

When thought-terminating cliche is NOT present:
- The phrase is used as a starting point, not an endpoint
- Further analysis follows the statement
- The cliche is acknowledged as a simplification
- The statement genuinely resolves the question with evidence
- The phrase is used ironically or self-awarely
- The response engages with the substance of the question
- Uncertainty is acknowledged rather than papered over

Output JSON with: thought_terminating_present (bool), severity (none/mild/moderate/severe), cliche (the phrase used), inquiry_blocked (what question is being shut down), false_resolution (what false sense of closure is created), deeper_question (what should be asked instead), recommendation (no_thought_termination/mild_oversimplification/significant_thought_termination/major_inquiry_suppression/continue_questioning)."""

THOUGHT_TERMINATING_PROMPT = """Detect thought-terminating cliche:

Statement: {statement}
Question addressed: {question}
Response given: {response}
Further inquiry: {further_inquiry}
Domain: {domain}
Context: {context}

Does this use stock phrases to shut down critical thinking? Return ONLY valid JSON."""


class ThoughtTerminatingClicheService:
    """Detects thought-terminating cliches — phrases that end critical thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        question: str = "",
        response: str = "",
        further_inquiry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect thought-terminating cliche."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=THOUGHT_TERMINATING_PROMPT.format(
                statement=statement,
                question=question or "Not specified",
                response=response or "Not specified",
                further_inquiry=further_inquiry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=THOUGHT_TERMINATING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "thought_terminating_present": data.get("thought_terminating_present", False),
            "severity": data.get("severity", ""),
            "cliche": data.get("cliche", ""),
            "inquiry_blocked": data.get("inquiry_blocked", ""),
            "deeper_question": data.get("deeper_question", ""),
            "recommendation": data.get("recommendation", ""),
        }

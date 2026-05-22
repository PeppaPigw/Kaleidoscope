"""SemanticStopsignService — Semantic Stopsign Detection.

Detects semantic stopsigns — words or phrases that halt further
inquiry by providing the illusion of explanation. "It's natural,"
"it's God's will," "it's just human nature," "the market decided"
— these feel like explanations but actually prevent deeper
investigation. They're cached thoughts that block curiosity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SEMANTIC_STOPSIGN_SYSTEM = """You are a semantic stopsign specialist. Given an explanation or justification, assess whether it halts inquiry rather than advancing it:

Key concepts (Yudkowsky, 2007):
- Semantic stopsign: words that halt further questioning
- Curiosity stopper: explanation that prevents deeper investigation
- Cached thought: pre-packaged answer that blocks fresh thinking
- Fake explanation: feels like understanding without providing mechanism
- Mystery as answer: "it's a mystery" presented as explanation
- Appeal to nature: "it's natural" as if that settles the question
- Deepity: statement that sounds profound but is either trivially true or false

When semantic stopsigns ARE present:
- "It's just human nature" (stops asking why)
- "The market decided" (anthropomorphizes, stops mechanism inquiry)
- "It's God's will" (halts causal investigation)
- "It's natural" (conflates is with ought, stops evaluation)
- "That's just how things are" (normalizes, prevents questioning)
- "It's complicated" (used to avoid rather than begin explanation)
- "Science can't explain everything" (used to stop specific inquiry)

When these phrases ARE appropriate:
- Used as starting points for further investigation, not endpoints
- Acknowledged as placeholders pending deeper understanding
- The speaker can elaborate on mechanism when pressed
- Used in contexts where further inquiry isn't productive
- The phrase accurately summarizes a well-understood mechanism

Output JSON with: semantic_stopsign_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is given), stopsign_phrase (what phrase halts inquiry), question_blocked (what further question is being prevented), deeper_mechanism (what mechanism could be investigated), inquiry_value (would further inquiry be productive), alternative_framing (how could this be framed to enable inquiry), recommendation (explanation_adequate/mild_curiosity_dampening/significant_semantic_stopsign/major_inquiry_blockage/continue_investigating)."""

SEMANTIC_STOPSIGN_PROMPT = """Detect semantic stopsign:

Explanation: {explanation}
Question asked: {question}
Response: {response}
Further inquiry: {further_inquiry}
Domain: {domain}
Context: {context}

Is a word or phrase halting further inquiry by providing the illusion of explanation? Return ONLY valid JSON."""


class SemanticStopsignService:
    """Detects semantic stopsigns — phrases that halt inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        question: str = "",
        response: str = "",
        further_inquiry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect semantic stopsign."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SEMANTIC_STOPSIGN_PROMPT.format(
                explanation=explanation,
                question=question or "Not specified",
                response=response or "Not specified",
                further_inquiry=further_inquiry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SEMANTIC_STOPSIGN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "semantic_stopsign_present": data.get("semantic_stopsign_present", False),
            "severity": data.get("severity", ""),
            "stopsign_phrase": data.get("stopsign_phrase", ""),
            "question_blocked": data.get("question_blocked", ""),
            "deeper_mechanism": data.get("deeper_mechanism", ""),
            "inquiry_value": data.get("inquiry_value", ""),
            "alternative_framing": data.get("alternative_framing", ""),
            "recommendation": data.get("recommendation", ""),
        }

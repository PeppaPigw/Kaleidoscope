"""CurseOfKnowledgeCommService — Curse of Knowledge (Communication) Detection.

Detects curse of knowledge in communication — the inability to
communicate simply because you cannot un-know what you know. The
expert's knowledge makes it impossible to reconstruct the novice's
perspective. Camerer, Loewenstein & Weber (1989).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CURSE_KNOWLEDGE_COMM_SYSTEM = """You are a curse of knowledge communication specialist. Given a communication, assess whether the communicator's expertise is preventing effective communication:

Key concepts (Camerer, Loewenstein & Weber, 1989):
- Curse of knowledge: can't un-know what you know
- Expert blind spot: experts forget what it's like not to know
- Hindsight bias in communication: "it's obvious" when it's not
- Abstraction level mismatch: expert thinks in abstractions, novice needs concrete
- Jargon blindness: using technical terms without realizing they're technical
- Compression: experts compress complex ideas into single words
- Empathic gap: inability to model the novice's mental state

When curse of knowledge IS present:
- Expert uses jargon without realizing it's jargon
- Explanations skip "obvious" steps that aren't obvious to the audience
- The communicator is frustrated by "simple" questions
- Abstract concepts are used without concrete grounding
- The explanation would only make sense to someone who already understands
- "As everyone knows..." for things not everyone knows
- The communicator can't identify what's confusing about their explanation

When communication IS accessible:
- The communicator actively models the audience's knowledge state
- Jargon is defined or replaced with plain language
- Concrete examples ground abstract concepts
- The explanation builds from what the audience knows
- Questions are welcomed and addressed without condescension
- The communicator can identify potential confusion points
- Feedback is sought and incorporated

Output JSON with: curse_of_knowledge_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), expertise_level (communicator's expertise), audience_level (audience's likely level), gap_indicators (what indicates the gap), accessibility (how accessible is the communication), recommendation (communication_accessible/mild_expert_blindspot/significant_curse_of_knowledge/major_communication_barrier/simplify_and_ground)."""

CURSE_KNOWLEDGE_COMM_PROMPT = """Detect curse of knowledge in communication:

Communication: {communication}
Communicator expertise: {expertise}
Audience: {audience}
Comprehension: {comprehension}
Domain: {domain}
Context: {context}

Is the communicator's expertise preventing effective communication? Return ONLY valid JSON."""


class CurseOfKnowledgeCommService:
    """Detects curse of knowledge in communication — expertise preventing clarity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        expertise: str = "",
        audience: str = "",
        comprehension: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curse of knowledge in communication."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CURSE_KNOWLEDGE_COMM_PROMPT.format(
                communication=communication,
                expertise=expertise or "Not specified",
                audience=audience or "Not specified",
                comprehension=comprehension or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CURSE_KNOWLEDGE_COMM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "curse_of_knowledge_present": data.get("curse_of_knowledge_present", False),
            "severity": data.get("severity", ""),
            "expertise_level": data.get("expertise_level", ""),
            "audience_level": data.get("audience_level", ""),
            "gap_indicators": data.get("gap_indicators", ""),
            "recommendation": data.get("recommendation", ""),
        }

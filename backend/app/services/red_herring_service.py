"""RedHerringService — Red Herring Detection.

Detects red herring — introducing irrelevant information or
arguments to divert attention from the actual issue being
discussed. The distraction may be interesting or emotionally
compelling but does not address the original question.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RED_HERRING_SYSTEM = """You are a red herring specialist. Given a discussion or argument, assess whether irrelevant information is being introduced to divert from the actual issue:

Key concepts:
- Red herring: introducing irrelevant material to divert attention
- Ignoratio elenchi: proving something other than what's at issue
- Topic shift: moving from the actual question to a different one
- Emotional distraction: using feelings to avoid addressing the argument
- Whataboutism: deflecting by pointing to someone else's behavior
- Scope creep: gradually expanding the topic to avoid the core issue
- Relevance: whether information actually bears on the conclusion

When red herring IS present:
- The response addresses a different question than what was asked
- Emotionally compelling but logically irrelevant information is introduced
- "We should discuss X" when the topic is Y
- Changing the subject when pressed on a weak point
- Introducing true but irrelevant facts to create confusion
- Answering a question that wasn't asked
- Using anecdotes that don't address the statistical argument

When red herring is NOT present:
- The information is genuinely relevant to the issue
- The topic shift is acknowledged and justified
- Background context is provided that bears on the conclusion
- The response addresses the actual question asked
- Analogies are used that illuminate the core issue
- The discussion naturally evolves to related topics
- Multiple relevant considerations are being weighed

Output JSON with: red_herring_present (bool), severity (none/mild/moderate/severe), original_issue (what the actual topic is), diversion (what irrelevant material was introduced), relevance (how the diversion relates or doesn't relate), motive (why the diversion might be introduced), recommendation (no_diversion/mild_tangent/significant_red_herring/major_topic_avoidance/return_to_original_issue)."""

RED_HERRING_PROMPT = """Detect red herring:

Discussion: {discussion}
Original issue: {original_issue}
Response given: {response}
Relevance: {relevance}
Domain: {domain}
Context: {context}

Does this introduce irrelevant information to divert from the actual issue? Return ONLY valid JSON."""


class RedHerringService:
    """Detects red herring — irrelevant diversions from the actual issue."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discussion: str,
        *,
        original_issue: str = "",
        response: str = "",
        relevance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect red herring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RED_HERRING_PROMPT.format(
                discussion=discussion,
                original_issue=original_issue or "Not specified",
                response=response or "Not specified",
                relevance=relevance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RED_HERRING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discussion": discussion[:200],
            "red_herring_present": data.get("red_herring_present", False),
            "severity": data.get("severity", ""),
            "original_issue": data.get("original_issue", ""),
            "diversion": data.get("diversion", ""),
            "relevance": data.get("relevance", ""),
            "recommendation": data.get("recommendation", ""),
        }

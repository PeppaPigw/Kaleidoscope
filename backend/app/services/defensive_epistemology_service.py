"""DefensiveEpistemologyService — Defensive Epistemology Detection.

Detects defensive epistemology — defensive postures that prevent
learning from criticism, where protecting beliefs takes priority
over improving understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEFENSIVE_EPISTEMOLOGY_SYSTEM = """You are a defensive epistemology specialist. Given a response to criticism, assess whether defensiveness is preventing learning:

Key concepts:
- Defensive epistemology: defensiveness preventing learning
- Criticism deflection: deflecting rather than engaging criticism
- Belief protection: protecting beliefs over improving understanding
- Counter-attack response: responding to criticism with attack
- Dismissal reflex: automatically dismissing challenges
- Fortress mentality: treating all criticism as attack
- Learning prevention: defensiveness blocking improvement

When defensive epistemology IS present:
- Defensiveness preventing engagement with criticism
- Criticism deflected rather than considered
- Belief protection prioritized over learning
- Counter-attacks substituting for engagement
- Challenges automatically dismissed
- All criticism treated as hostile attack
- Defensiveness blocking potential improvement

When appropriate defense is present:
- Criticism engaged before being rejected
- Defense based on evidence not reflex
- Beliefs defended with reasons not deflection
- Challenges considered before responding
- Dismissal based on evaluation not reflex
- Criticism distinguished from attack
- Defense serving truth not comfort

Output JSON with: defensiveness_present (bool), severity (none/mild/moderate/severe), criticism (what criticism is received), response (how it is responded to), learning_blocked (what learning is prevented), pattern (what defensive pattern exists), recommendation (engaged_response/mild_defensiveness/significant_defensive_epistemology/major_learning_prevention/engage_criticism_before_defending)."""

DEFENSIVE_EPISTEMOLOGY_PROMPT = """Detect defensive epistemology:

Criticism received: {criticism}
Response pattern: {response}
Engagement level: {engagement}
Learning outcome: {learning}
Domain: {domain}
Context: {context}

Is defensiveness preventing learning from criticism? Return ONLY valid JSON."""


class DefensiveEpistemologyService:
    """Detects defensive epistemology — defensiveness preventing learning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        criticism: str,
        *,
        response: str = "",
        engagement: str = "",
        learning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect defensive epistemology."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEFENSIVE_EPISTEMOLOGY_PROMPT.format(
                criticism=criticism,
                response=response or "Not specified",
                engagement=engagement or "Not specified",
                learning=learning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEFENSIVE_EPISTEMOLOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "criticism": criticism[:200],
            "defensiveness_present": data.get("defensiveness_present", False),
            "severity": data.get("severity", ""),
            "response": data.get("response", ""),
            "learning_blocked": data.get("learning_blocked", ""),
            "pattern": data.get("pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""TuQuoqueService — Tu Quoque Detection.

Detects tu quoque (you too) — deflecting criticism by pointing to
the critic's own behavior rather than addressing the substance of
the criticism. The critic's hypocrisy doesn't make their argument
wrong, but it's used as if it does.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TU_QUOQUE_SYSTEM = """You are a tu quoque specialist. Given a response to criticism, assess whether it deflects by pointing to the critic's behavior rather than addressing the argument:

Key concepts:
- Tu quoque: "you do it too" as deflection
- Hypocrisy charge: attacking the messenger's consistency
- Whataboutism overlap: "what about when you..."
- Ad hominem variant: attacking the critic rather than the criticism
- Genetic fallacy: judging argument by who makes it
- Deflection: changing subject from the criticism to the critic
- Relevance: the critic's behavior doesn't affect the argument's validity

When tu quoque IS present:
- "You're one to talk" without addressing the point
- Pointing to the critic's past behavior as a rebuttal
- "What about when you did X?" as a response to criticism
- Using hypocrisy charges to avoid engaging with substance
- Deflecting from the argument to the arguer's consistency
- "You can't criticize X because you also do Y"
- Treating the critic's imperfection as a refutation

When pointing out hypocrisy IS appropriate:
- The criticism is specifically about moral authority or standing
- The hypocrisy is addressed alongside the substance
- The inconsistency reveals something about the argument itself
- It's offered as additional context, not as a complete rebuttal
- The critic's behavior is directly relevant to the specific claim
- Both the substance and the hypocrisy are addressed
- The goal is to establish fair standards, not to deflect

Output JSON with: tu_quoque_present (bool), severity (none/mild/moderate/severe), criticism (what criticism was made), response (how it was responded to), deflection (what behavior is pointed to), substance_addressed (is the original criticism addressed), relevance (is the critic's behavior relevant), recommendation (hypocrisy_relevant/mild_deflection/significant_tu_quoque/major_substance_avoidance/address_argument_not_arguer)."""

TU_QUOQUE_PROMPT = """Detect tu quoque:

Criticism: {criticism}
Response: {response}
Deflection: {deflection}
Substance: {substance}
Domain: {domain}
Context: {context}

Is criticism being deflected by pointing to the critic's own behavior rather than addressing the argument? Return ONLY valid JSON."""


class TuQuoqueService:
    """Detects tu quoque — deflecting criticism via hypocrisy charges."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        criticism: str,
        *,
        response: str = "",
        deflection: str = "",
        substance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tu quoque."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TU_QUOQUE_PROMPT.format(
                criticism=criticism,
                response=response or "Not specified",
                deflection=deflection or "Not specified",
                substance=substance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TU_QUOQUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "criticism": criticism[:200],
            "tu_quoque_present": data.get("tu_quoque_present", False),
            "severity": data.get("severity", ""),
            "deflection": data.get("deflection", ""),
            "substance_addressed": data.get("substance_addressed", ""),
            "relevance": data.get("relevance", ""),
            "recommendation": data.get("recommendation", ""),
        }

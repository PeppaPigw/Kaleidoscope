"""StrategicIgnoranceService — Strategic Ignorance Detection.

Detects strategic ignorance — deliberately avoiding information
that might obligate action or create discomfort. Grossman &
van der Weele (2017). "I'd rather not know." People avoid
learning things that would make them feel guilty, obligated,
or that would constrain their preferred behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_IGNORANCE_SYSTEM = """You are a strategic ignorance specialist. Given a situation where information is being avoided, assess whether the avoidance is strategic:

Key concepts (Grossman & van der Weele, 2017):
- Strategic ignorance: deliberately avoiding information
- Moral wiggle room: ignorance preserves plausible deniability
- Information avoidance: choosing not to learn uncomfortable truths
- Willful ignorance: knowing you could know but choosing not to
- Plausible deniability: "I didn't know" as excuse
- Motivated information avoidance: avoiding info that would obligate action
- Ostrich effect interaction: avoiding negative financial information

When strategic ignorance IS present:
- Deliberately not checking outcomes of decisions
- "I'd rather not know the details"
- Avoiding information that would create moral obligation
- Not reading terms/conditions to maintain ignorance
- Choosing not to learn about consequences of actions
- "What I don't know can't hurt me" as strategy
- Avoiding feedback that might require change

When information avoidance IS appropriate:
- The information is genuinely irrelevant to decisions
- Information overload makes selective attention necessary
- The person has delegated the decision appropriately
- Privacy boundaries justify not seeking information
- The information would cause harm without enabling action

Output JSON with: strategic_ignorance_present (bool), severity (none/mild/moderate/severe), situation (what information is being avoided), avoided_info (what specific information is being avoided), motivation (why is it being avoided), obligation_avoided (what obligation would the information create), plausible_deniability (is deniability being maintained), cost_of_knowing (what would knowing cost), recommendation (avoidance_appropriate/mild_strategic_ignorance/significant_information_avoidance/major_willful_ignorance/seek_the_information)."""

STRATEGIC_IGNORANCE_PROMPT = """Detect strategic ignorance:

Situation: {situation}
Avoided information: {avoided}
Motivation: {motivation}
Consequences: {consequences}
Domain: {domain}
Context: {context}

Is information being deliberately avoided to maintain plausible deniability or avoid obligation? Return ONLY valid JSON."""


class StrategicIgnoranceService:
    """Detects strategic ignorance — deliberately avoiding obligating information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        avoided: str = "",
        motivation: str = "",
        consequences: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_IGNORANCE_PROMPT.format(
                situation=situation,
                avoided=avoided or "Not specified",
                motivation=motivation or "Not specified",
                consequences=consequences or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "strategic_ignorance_present": data.get("strategic_ignorance_present", False),
            "severity": data.get("severity", ""),
            "avoided_info": data.get("avoided_info", ""),
            "motivation": data.get("motivation", ""),
            "obligation_avoided": data.get("obligation_avoided", ""),
            "plausible_deniability": data.get("plausible_deniability", ""),
            "cost_of_knowing": data.get("cost_of_knowing", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""SocialLoafingService — Social Loafing Detection.

Detects social loafing — tendency for individuals to exert
less effort when working collectively than when working alone.
Latané, Williams & Harkins (1979). People pull less hard on
a rope when in a group. Individual effort decreases as group
size increases when contributions are pooled.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SOCIAL_LOAFING_SYSTEM = """You are a social loafing specialist. Given a group work situation, assess whether individuals are reducing effort because their contribution is pooled:

Key concepts (Latané, Williams & Harkins, 1979):
- Social loafing: reduced effort in collective tasks
- Free riding: benefiting from group output without contributing
- Sucker effect: reducing effort because others are loafing
- Evaluation apprehension: less effort when individual output isn't evaluated
- Dispensability: feeling one's contribution doesn't matter
- Identifiability: effort increases when individual contribution is visible
- Social compensation: some members increase effort to compensate

When social loafing IS present:
- Less effort in group projects than individual ones
- "My contribution won't be noticed anyway"
- Uneven workload distribution in teams
- Reduced quality when work is pooled vs individual
- Hiding behind group output
- "The team will pick up the slack"
- Effort that decreases as team size increases

When reduced effort IS appropriate:
- The task genuinely requires less from each person in a larger group
- Division of labor means each person does their specialized part
- The person is appropriately delegating
- Individual contributions are tracked and evaluated
- The reduced effort reflects efficient collaboration

Output JSON with: social_loafing_present (bool), severity (none/mild/moderate/severe), situation (what group work is happening), group_size (how large is the group), individual_effort (what effort is each person contributing), identifiability (can individual contributions be identified), evaluation (is individual performance evaluated), dispensability_belief (does the person feel dispensable), recommendation (effort_appropriate/mild_loafing/significant_free_riding/major_social_loafing/increase_identifiability)."""

SOCIAL_LOAFING_PROMPT = """Detect social loafing:

Situation: {situation}
Team: {team}
Effort: {effort}
Evaluation: {evaluation}
Domain: {domain}
Context: {context}

Are individuals reducing effort because their contribution is pooled? Return ONLY valid JSON."""


class SocialLoafingService:
    """Detects social loafing — reduced individual effort in group settings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        team: str = "",
        effort: str = "",
        evaluation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect social loafing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SOCIAL_LOAFING_PROMPT.format(
                situation=situation,
                team=team or "Not specified",
                effort=effort or "Not specified",
                evaluation=evaluation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SOCIAL_LOAFING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "social_loafing_present": data.get("social_loafing_present", False),
            "severity": data.get("severity", ""),
            "group_size": data.get("group_size", ""),
            "individual_effort": data.get("individual_effort", ""),
            "identifiability": data.get("identifiability", ""),
            "evaluation": data.get("evaluation", ""),
            "dispensability_belief": data.get("dispensability_belief", ""),
            "recommendation": data.get("recommendation", ""),
        }

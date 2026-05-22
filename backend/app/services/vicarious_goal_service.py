"""VicariousGoalService — Vicarious Goal Fulfillment Detection.

Detects vicarious goal fulfillment — the phenomenon where
announcing or planning goals provides enough psychological
satisfaction to reduce motivation to actually achieve them.
Gollwitzer et al. (2009). Telling others about your intentions
creates a premature sense of completeness that undermines follow-through.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VICARIOUS_GOAL_SYSTEM = """You are a vicarious goal fulfillment specialist. Given a goal-related situation, assess whether announcing or planning is substituting for actual achievement:

Key concepts (Gollwitzer et al., 2009):
- Vicarious goal fulfillment: announcing goals satisfies the drive
- Identity-related goals: most vulnerable to this effect
- Social reality: others acknowledging your goal makes it feel real
- Premature completeness: planning feels like doing
- Intention-behavior gap: strong intentions, weak follow-through
- Symbolic self-completion: symbols of identity substitute for substance
- Planning fallacy interaction: detailed plans feel like progress

When vicarious goal fulfillment IS present:
- Extensive goal announcement without proportional action
- Detailed planning that never transitions to execution
- Social media declarations substituting for behavior change
- Buying equipment/tools as substitute for using them
- Research and preparation that never ends
- "I'm going to..." repeated without "I did..."
- Identity claims without supporting behavior

When goal communication IS appropriate:
- Accountability partnerships with follow-up mechanisms
- Implementation intentions (when/where/how specifics)
- Progress reporting on actual milestones
- Seeking specific help or resources for execution
- The announcement includes concrete commitment devices
- Past pattern shows announcement leads to action

Output JSON with: vicarious_fulfillment_present (bool), severity (none/mild/moderate/severe), goal (what is the stated goal), announcement (how was it communicated), action_taken (what actual steps followed), identity_relevance (how identity-linked is the goal), completion_feeling (does announcing feel like achieving), accountability (are there follow-up mechanisms), recommendation (communication_productive/mild_substitution/significant_vicarious_fulfillment/major_announcement_as_achievement/implement_commitment_devices)."""

VICARIOUS_GOAL_PROMPT = """Detect vicarious goal fulfillment:

Goal: {goal}
Communication: {communication}
Action: {action}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is announcing or planning the goal substituting for actually achieving it? Return ONLY valid JSON."""


class VicariousGoalService:
    """Detects vicarious goal fulfillment — announcing substituting for achieving."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        goal: str,
        *,
        communication: str = "",
        action: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect vicarious goal fulfillment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VICARIOUS_GOAL_PROMPT.format(
                goal=goal,
                communication=communication or "Not specified",
                action=action or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=VICARIOUS_GOAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "goal": goal[:200],
            "vicarious_fulfillment_present": data.get("vicarious_fulfillment_present", False),
            "severity": data.get("severity", ""),
            "announcement": data.get("announcement", ""),
            "action_taken": data.get("action_taken", ""),
            "identity_relevance": data.get("identity_relevance", ""),
            "completion_feeling": data.get("completion_feeling", ""),
            "accountability": data.get("accountability", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""ReversibilityService — Decision Reversibility Assessment.

Assesses how reversible a decision or action is. Irreversible decisions
need more evidence and deliberation than reversible ones. Identifies
lock-in effects, path dependencies, and exit costs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REVERSIBILITY_SYSTEM = """You are a reversibility analyst. Given a decision or action, assess how reversible it is:
- Can you undo it completely, partially, or not at all?
- What's the cost of reversal (time, money, reputation, relationships)?
- Are there lock-in effects or path dependencies?
- At what point does it become irreversible (point of no return)?
- What information would you want before committing?
- Is there a way to make it more reversible (pilot, staged rollout, options)?

Output JSON with: reversibility_score (0-1, where 1=fully reversible), reversal_cost (negligible/low/moderate/high/prohibitive), lock_in_effects (list of: effect, severity (minor/moderate/major/permanent), when_it_kicks_in), point_of_no_return (description of when reversal becomes impossible), path_dependencies (list of future options foreclosed by this decision), information_needed (what you'd want to know before committing), ways_to_increase_reversibility (list of: strategy, how_it_helps), time_pressure_real (bool — is the urgency genuine or manufactured?), comparable_decisions (similar decisions and how reversible they turned out to be), recommendation (commit/pilot_first/keep_options_open/delay_until_more_info/avoid), decision_category (one_way_door/two_way_door/revolving_door)."""

REVERSIBILITY_PROMPT = """Assess reversibility:

Decision: {decision}
Context: {context}
Domain: {domain}
Stakes: {stakes}
Time pressure: {time_pressure}

How reversible is this? Return ONLY valid JSON."""


class ReversibilityService:
    """Assesses decision reversibility and lock-in effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        decision: str,
        *,
        context: str = "",
        domain: str = "",
        stakes: str = "",
        time_pressure: str = "",
    ) -> dict:
        """Assess decision reversibility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REVERSIBILITY_PROMPT.format(
                decision=decision,
                context=context or "No additional context",
                domain=domain or "general",
                stakes=stakes or "Not specified",
                time_pressure=time_pressure or "Not specified",
            ),
            system=REVERSIBILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "reversibility_score": data.get("reversibility_score", 0),
            "reversal_cost": data.get("reversal_cost", ""),
            "lock_in_effects": data.get("lock_in_effects", []),
            "point_of_no_return": data.get("point_of_no_return", ""),
            "path_dependencies": data.get("path_dependencies", []),
            "information_needed": data.get("information_needed", ""),
            "ways_to_increase_reversibility": data.get("ways_to_increase_reversibility", []),
            "time_pressure_real": data.get("time_pressure_real", True),
            "comparable_decisions": data.get("comparable_decisions", []),
            "recommendation": data.get("recommendation", ""),
            "decision_category": data.get("decision_category", ""),
        }

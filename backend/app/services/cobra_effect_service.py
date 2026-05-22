"""CobraEffectService — Perverse Solution & Backfire Detection.

Identifies when a proposed solution is likely to make the problem
worse. Named after the Delhi cobra bounty that incentivized cobra
breeding. Detects solutions that create the problem they aim to solve.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COBRA_SYSTEM = """You are a cobra effect specialist. Given a proposed solution, assess whether it might backfire and make the problem worse:
- Could the solution create incentives that worsen the original problem?
- Are there gaming/exploitation vectors?
- Could it trigger compensating behavior that negates the benefit?
- Are there historical examples of similar solutions backfiring?
- What's the mechanism by which it could make things worse?

Output JSON with: backfire_risk (0-1), backfire_mechanisms (list of: mechanism, how_it_worsens_problem, likelihood (0-1)), gaming_vectors (list of: who_games, how_they_game, what_happens), compensating_behaviors (list of behaviors that negate the solution), historical_cobra_effects (list of: situation, intended_effect, actual_effect), problem_displacement (does it just move the problem elsewhere?), displacement_target (where the problem moves to), net_effect_estimate (positive/neutral/negative/catastrophic), conditions_for_backfire (what must be true for backfire to occur), conditions_for_success (what must be true for solution to work), safeguards (list of: safeguard, what_it_prevents), recommendation (implement/implement_with_safeguards/pilot_first/redesign/abandon), better_approach (alternative that avoids the cobra effect)."""

COBRA_PROMPT = """Detect cobra effect / backfire risk:

Problem: {problem}
Proposed solution: {solution}
Domain: {domain}
Actors involved: {actors}
Context: {context}

Could this solution make things worse? Return ONLY valid JSON."""


class CobraEffectService:
    """Detects solutions that might backfire and worsen the problem."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        problem: str,
        solution: str,
        *,
        actors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cobra effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COBRA_PROMPT.format(
                problem=problem,
                solution=solution,
                actors=actors or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COBRA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:150],
            "solution": solution[:150],
            "backfire_risk": data.get("backfire_risk", 0),
            "backfire_mechanisms": data.get("backfire_mechanisms", []),
            "gaming_vectors": data.get("gaming_vectors", []),
            "compensating_behaviors": data.get("compensating_behaviors", []),
            "historical_cobra_effects": data.get("historical_cobra_effects", []),
            "problem_displacement": data.get("problem_displacement", False),
            "displacement_target": data.get("displacement_target", ""),
            "net_effect_estimate": data.get("net_effect_estimate", ""),
            "conditions_for_backfire": data.get("conditions_for_backfire", ""),
            "conditions_for_success": data.get("conditions_for_success", ""),
            "safeguards": data.get("safeguards", []),
            "recommendation": data.get("recommendation", ""),
            "better_approach": data.get("better_approach", ""),
        }

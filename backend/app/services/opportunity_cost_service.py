"""OpportunityCostService — Opportunity Cost & Path-Not-Taken Analysis.

When evaluating a choice, identifies what you're giving up.
Maps the unseen costs of the path not taken, including time,
attention, optionality, and second-order effects.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OPPORTUNITY_SYSTEM = """You are an opportunity cost analyst. Given a choice or allocation of resources, identify what's being given up:
- What alternatives are foreclosed?
- What's the best alternative use of these resources (time, money, attention)?
- Are there hidden costs beyond the obvious ones?
- What optionality is being consumed?
- What's the cost of the attention/focus being spent here?

Output JSON with: chosen_path (what's being done), best_alternative (the strongest path not taken), opportunity_cost_estimate (qualitative: negligible/low/moderate/high/enormous), hidden_costs (list of: cost, magnitude, why_hidden), optionality_consumed (list of future options foreclosed), attention_cost (what else could this focus accomplish), time_cost (what the time could produce elsewhere), reversibility_if_wrong (how hard to switch to alternative later), alternatives_ranked (list of: alternative, value_estimate, why_not_chosen), total_cost_visibility (0-1, how much of the true cost is visible to the decision-maker), recommendation (proceed/reconsider/explore_alternatives/defer), key_question (the one question that would clarify whether this is the right allocation)."""

OPPORTUNITY_PROMPT = """Analyze opportunity costs:

Choice: {choice}
Resources committed: {resources}
Alternatives considered: {alternatives}
Domain: {domain}
Context: {context}

What's being given up? Return ONLY valid JSON."""


class OpportunityCostService:
    """Analyzes opportunity costs and paths not taken."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        choice: str,
        *,
        resources: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze opportunity costs."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPPORTUNITY_PROMPT.format(
                choice=choice,
                resources=resources or "Not specified",
                alternatives=alternatives or "Not explicitly considered",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OPPORTUNITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choice": choice[:200],
            "chosen_path": data.get("chosen_path", ""),
            "best_alternative": data.get("best_alternative", ""),
            "opportunity_cost_estimate": data.get("opportunity_cost_estimate", ""),
            "hidden_costs": data.get("hidden_costs", []),
            "optionality_consumed": data.get("optionality_consumed", []),
            "attention_cost": data.get("attention_cost", ""),
            "time_cost": data.get("time_cost", ""),
            "reversibility_if_wrong": data.get("reversibility_if_wrong", ""),
            "alternatives_ranked": data.get("alternatives_ranked", []),
            "total_cost_visibility": data.get("total_cost_visibility", 0),
            "recommendation": data.get("recommendation", ""),
            "key_question": data.get("key_question", ""),
        }

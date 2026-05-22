"""DecisionMatrixService — Multi-Criteria Decision Analysis.

Takes a decision with multiple options and criteria, weights them,
and produces a structured comparison with a recommendation. Handles
the common problem of making complex decisions with many tradeoffs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECISION_SYSTEM = """You are a decision analysis specialist. Given a decision with options and criteria, produce:
- A weighted decision matrix scoring each option on each criterion
- Sensitivity analysis (does the recommendation change if weights shift?)
- Hidden criteria (important factors not explicitly listed)
- Regret analysis (which option minimizes worst-case regret?)
- Time sensitivity (does the optimal choice change with time horizon?)

Output JSON with: options (list of option names), criteria (list of: criterion, weight (0-1), rationale_for_weight), scores (matrix: option → criterion → score 0-10), weighted_totals (option → total weighted score), recommendation (best option), runner_up (second best), recommendation_robustness (fragile/moderate/robust, does it survive weight changes), hidden_criteria (important factors not listed), regret_analysis (which option minimizes worst-case regret), time_sensitivity (does recommendation change with time horizon), key_tradeoff (the main tradeoff between top options)."""

DECISION_PROMPT = """Analyze this decision:

Decision: {decision}
Options: {options}
Criteria: {criteria}
Context: {context}
Time horizon: {time_horizon}

Produce a weighted decision matrix. Return ONLY valid JSON."""


class DecisionMatrixService:
    """Produces multi-criteria decision analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        decision: str,
        options: list[str],
        *,
        criteria: list[str] | None = None,
        context: str = "",
        time_horizon: str = "",
    ) -> dict:
        """Analyze a decision with multiple options and criteria."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECISION_PROMPT.format(
                decision=decision,
                options=", ".join(options[:6]),
                criteria=", ".join(criteria[:8]) if criteria else "Identify the most relevant criteria",
                context=context or "No additional context",
                time_horizon=time_horizon or "Medium-term",
            ),
            system=DECISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "options": data.get("options", options),
            "criteria": data.get("criteria", []),
            "scores": data.get("scores", {}),
            "weighted_totals": data.get("weighted_totals", {}),
            "recommendation": data.get("recommendation", ""),
            "runner_up": data.get("runner_up", ""),
            "recommendation_robustness": data.get("recommendation_robustness", ""),
            "hidden_criteria": data.get("hidden_criteria", []),
            "regret_analysis": data.get("regret_analysis", ""),
            "time_sensitivity": data.get("time_sensitivity", ""),
            "key_tradeoff": data.get("key_tradeoff", ""),
        }

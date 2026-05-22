"""ErgodicityService — Ergodicity Assessment.

Evaluates whether a system or strategy is ergodic (time average
equals ensemble average) or non-ergodic. In non-ergodic systems,
what works for the group doesn't work for the individual over time.
Russian roulette has positive expected value but is non-ergodic —
you can't play it repeatedly. Critical for understanding when
expected value calculations are misleading.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ERGODICITY_SYSTEM = """You are an ergodicity specialist. Given a strategy or system, assess whether it is ergodic:
- Does the time average equal the ensemble average?
- Can an individual repeatedly engage with this system and expect the average outcome?
- Are there absorbing barriers (ruin, death, bankruptcy) that make repeated play impossible?
- Is the expected value calculation misleading because it assumes ergodicity?
- Would the Kelly criterion suggest a different strategy than expected value maximization?

Output JSON with: ergodic (bool — is this system ergodic?), non_ergodicity_type (none/absorbing_barrier/path_dependent/multiplicative/irreversible), ensemble_average (what the average outcome looks like across many participants), time_average (what the outcome looks like for one participant over time), divergence (how much ensemble and time averages differ), absorbing_barriers (what states end the game: bankruptcy, death, ruin, etc), ruin_probability (0-1 — probability of hitting an absorbing barrier), expected_value_misleading (bool — is EV calculation giving wrong intuition?), kelly_fraction (what fraction of resources should be risked per round), naive_strategy_risk (what happens if you follow the EV-maximizing strategy), optimal_strategy (what strategy accounts for non-ergodicity), leverage_effect (does leverage make non-ergodicity worse?), time_horizon_matters (bool — does the answer change with time horizon?), who_benefits_from_ergodicity_confusion (who profits when people treat non-ergodic systems as ergodic?), real_world_examples (similar systems and their ergodicity properties), recommendation (treat_as_ergodic/size_positions_carefully/avoid_ruin/reduce_variance/accept_lower_ev_for_survival)."""

ERGODICITY_PROMPT = """Assess ergodicity:

Strategy/System: {strategy}
Payoff structure: {payoffs}
Repetition: {repetition}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Is this ergodic? Return ONLY valid JSON."""


class ErgodicityService:
    """Assesses ergodicity — whether time averages equal ensemble averages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        strategy: str,
        *,
        payoffs: str = "",
        repetition: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess ergodicity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ERGODICITY_PROMPT.format(
                strategy=strategy,
                payoffs=payoffs or "Not specified",
                repetition=repetition or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ERGODICITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategy": strategy[:200],
            "ergodic": data.get("ergodic", False),
            "non_ergodicity_type": data.get("non_ergodicity_type", ""),
            "ensemble_average": data.get("ensemble_average", ""),
            "time_average": data.get("time_average", ""),
            "divergence": data.get("divergence", ""),
            "absorbing_barriers": data.get("absorbing_barriers", []),
            "ruin_probability": data.get("ruin_probability", 0),
            "expected_value_misleading": data.get("expected_value_misleading", False),
            "kelly_fraction": data.get("kelly_fraction", ""),
            "naive_strategy_risk": data.get("naive_strategy_risk", ""),
            "optimal_strategy": data.get("optimal_strategy", ""),
            "leverage_effect": data.get("leverage_effect", ""),
            "time_horizon_matters": data.get("time_horizon_matters", False),
            "who_benefits_from_ergodicity_confusion": data.get("who_benefits_from_ergodicity_confusion", ""),
            "real_world_examples": data.get("real_world_examples", []),
            "recommendation": data.get("recommendation", ""),
        }

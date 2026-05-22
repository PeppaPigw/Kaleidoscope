"""ProbabilityMatchingService — Probability Matching Detection.

Detects probability matching — tendency to match the frequency
of choices to the probability of outcomes rather than always
choosing the most likely outcome (maximizing). Vulkan (2000).
If option A wins 70% of the time, people choose A 70% and B
30% instead of always choosing A (which maximizes expected value).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROBABILITY_MATCHING_SYSTEM = """You are a probability matching specialist. Given a repeated decision under uncertainty, assess whether someone is matching probabilities rather than maximizing:

Key concepts (Vulkan, 2000):
- Probability matching: choosing options in proportion to their success rates
- Maximizing: always choosing the highest-probability option
- Suboptimal diversification: spreading choices when concentration is better
- Pattern seeking: trying to predict random sequences
- Win-stay/lose-shift: heuristic that approximates matching
- Exploration vs exploitation: matching as excessive exploration
- Gambler's fallacy interaction: trying to predict the next outcome

When probability matching IS present:
- Choosing the less likely option "because it's due"
- Spreading bets proportionally rather than concentrating on best
- "I'll pick B sometimes because it wins sometimes"
- Trying to predict random sequences rather than playing the odds
- Diversifying choices in repeated independent decisions
- Not always choosing the dominant strategy

When matching IS rational:
- The environment is adversarial (game theory)
- There are genuine benefits to exploration
- The probabilities are unknown and being learned
- Variety has intrinsic value in the context
- The person is deliberately randomizing for strategic reasons
- Outcomes are not independent (sequential dependence)

Output JSON with: probability_matching_present (bool), severity (none/mild/moderate/severe), decision (what repeated decision is being made), probabilities (what are the outcome probabilities), choice_pattern (how are choices being distributed), optimal_strategy (what would maximizing look like), expected_value_loss (how much EV is lost by matching), independence (are outcomes independent?), exploration_value (is there value in exploring?), recommendation (strategy_rational/mild_matching/significant_suboptimal/major_probability_matching/maximize_best_option)."""

PROBABILITY_MATCHING_PROMPT = """Detect probability matching:

Decision: {decision}
Probabilities: {probabilities}
Choice pattern: {pattern}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is someone matching probabilities rather than maximizing expected value? Return ONLY valid JSON."""


class ProbabilityMatchingService:
    """Detects probability matching — matching choice frequency to outcome probability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        probabilities: str = "",
        pattern: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect probability matching."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROBABILITY_MATCHING_PROMPT.format(
                decision=decision,
                probabilities=probabilities or "Not specified",
                pattern=pattern or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROBABILITY_MATCHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "probability_matching_present": data.get("probability_matching_present", False),
            "severity": data.get("severity", ""),
            "choice_pattern": data.get("choice_pattern", ""),
            "optimal_strategy": data.get("optimal_strategy", ""),
            "expected_value_loss": data.get("expected_value_loss", ""),
            "independence": data.get("independence", ""),
            "exploration_value": data.get("exploration_value", ""),
            "recommendation": data.get("recommendation", ""),
        }

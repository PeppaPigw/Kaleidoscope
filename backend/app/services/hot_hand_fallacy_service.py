"""HotHandFallacyService — Hot Hand Fallacy Detection.

Detects hot hand fallacy — believing that a streak of successes in
a random process means the next outcome is more likely to be a success.
While the original hot hand research has been partially revised,
the fallacy remains relevant when applied to genuinely random processes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HOT_HAND_SYSTEM = """You are a hot hand fallacy specialist. Given a prediction based on streaks, assess whether it commits the hot hand fallacy — expecting streaks to continue in random processes:

Key concepts:
- Hot hand fallacy: believing streaks predict future outcomes in random processes
- Streak perception: humans over-perceive streaks in random sequences
- Independence: in truly random processes, past doesn't predict future
- Skill vs luck: distinguishing processes where streaks are informative
- Momentum illusion: perceiving momentum in random fluctuations
- Regression to mean: extreme performance tends to regress
- Domain matters: hot hand may be real in some skill domains

When hot hand fallacy IS present:
- Expecting a winning streak to continue in a random process
- "They're on a roll" in contexts where outcomes are independent
- Investment decisions based on recent performance streaks
- Believing a random process has "momentum"
- Extrapolating short-term trends in noisy data
- "Due for a win/loss" reasoning (inverse hot hand = gambler's fallacy)
- Treating random variation as evidence of changing ability

When streak IS informative:
- The process genuinely involves skill that can vary
- There's evidence of state-dependent performance (fatigue, confidence)
- The domain has been shown to exhibit genuine hot hand effects
- The streak is long enough to be statistically significant
- Mechanism exists for why performance would be autocorrelated
- Base rates support that streaks in this domain are non-random
- The prediction accounts for regression to the mean

Output JSON with: hot_hand_fallacy_present (bool), severity (none/mild/moderate/severe), prediction (what is predicted), streak (what streak is observed), process_type (random/skill/mixed), independence (are outcomes independent), mechanism (is there a mechanism for streaks), recommendation (streak_informative/mild_hot_hand/significant_hot_hand_fallacy/major_momentum_illusion/check_process_independence)."""

HOT_HAND_PROMPT = """Detect hot hand fallacy:

Prediction: {prediction}
Streak observed: {streak}
Process type: {process_type}
Independence: {independence}
Domain: {domain}
Context: {context}

Is this prediction based on expecting a streak to continue in a random process? Return ONLY valid JSON."""


class HotHandFallacyService:
    """Detects hot hand fallacy — expecting streaks to continue in random processes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        streak: str = "",
        process_type: str = "",
        independence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hot hand fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HOT_HAND_PROMPT.format(
                prediction=prediction,
                streak=streak or "Not specified",
                process_type=process_type or "Not specified",
                independence=independence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HOT_HAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "hot_hand_fallacy_present": data.get("hot_hand_fallacy_present", False),
            "severity": data.get("severity", ""),
            "process_type": data.get("process_type", ""),
            "independence": data.get("independence", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""HotHandService — Hot Hand Fallacy Detection.

Detects hot hand fallacy — believing that a person who has
experienced success has a greater chance of further success
in additional attempts. Gilovich, Vallone & Tversky (1985).
"They're on a streak!" when outcomes are actually independent.
Seeing patterns in randomness and expecting streaks to continue.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HOT_HAND_SYSTEM = """You are a hot hand fallacy specialist. Given a judgment about sequential outcomes, assess whether someone is incorrectly perceiving streaks in independent events:

Key concepts (Gilovich, Vallone & Tversky, 1985):
- Hot hand fallacy: believing success breeds more success in independent events
- Streak perception: seeing patterns in random sequences
- Positive recency: expecting recent trends to continue
- Clustering illusion interaction: random clusters interpreted as streaks
- Gambler's fallacy inverse: expecting continuation rather than reversal
- Independence neglect: ignoring that each trial is independent
- Momentum belief: attributing causal power to recent outcomes

When hot hand fallacy IS present:
- "They're on a roll" in independent-outcome situations
- Betting more after wins in games of chance
- Expecting a stock to keep rising because it has been rising
- "They can't miss" after a series of successes
- Allocating more resources to recent winners without structural reason
- Hiring/promoting based on recent streak rather than base rate

When the pattern IS informative:
- Outcomes are genuinely dependent (skill improvement, learning curves)
- There is a structural reason for continuation (momentum in markets with feedback)
- The domain has genuine hot-hand effects (some sports contexts)
- Performance reflects changing skill level, not luck
- The streak reflects a genuine regime change

Output JSON with: hot_hand_present (bool), severity (none/mild/moderate/severe), judgment (what is being predicted), streak (what streak is being perceived), independence (are outcomes actually independent?), base_rate (what is the base rate of success?), structural_reason (is there a structural reason for continuation?), sample_size (how long is the streak?), alternative_explanation (what else could explain the pattern?), recommendation (pattern_informative/mild_streak_bias/significant_hot_hand/major_independence_neglect/assess_independence)."""

HOT_HAND_PROMPT = """Detect hot hand fallacy:

Judgment: {judgment}
Streak: {streak}
Outcomes: {outcomes}
Independence: {independence}
Domain: {domain}
Context: {context}

Is someone incorrectly expecting a streak to continue in independent events? Return ONLY valid JSON."""


class HotHandService:
    """Detects hot hand fallacy — expecting streaks to continue in independent events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        streak: str = "",
        outcomes: str = "",
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
                judgment=judgment,
                streak=streak or "Not specified",
                outcomes=outcomes or "Not specified",
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
            "judgment": judgment[:200],
            "hot_hand_present": data.get("hot_hand_present", False),
            "severity": data.get("severity", ""),
            "streak": data.get("streak", ""),
            "independence": data.get("independence", ""),
            "base_rate": data.get("base_rate", ""),
            "structural_reason": data.get("structural_reason", ""),
            "sample_size": data.get("sample_size", ""),
            "alternative_explanation": data.get("alternative_explanation", ""),
            "recommendation": data.get("recommendation", ""),
        }

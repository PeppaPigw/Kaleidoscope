"""GoldenMeanFallacyService — Golden Mean Fallacy Detection.

Detects the golden mean fallacy (argument to moderation) — assuming
the truth must lie between two extreme positions. The middle ground
between a correct position and an incorrect position is not
necessarily correct. Compromise between truth and falsehood is
not truth — it's just a different falsehood.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOLDEN_MEAN_FALLACY_SYSTEM = """You are a golden mean fallacy specialist. Given a dispute resolution or position-taking, assess whether the middle ground is being assumed correct simply because it's in the middle:

Key concepts:
- Golden mean fallacy: truth must be between extremes
- Argument to moderation: compromise position = correct position
- False middle: the midpoint between right and wrong isn't right
- Centrism bias: assuming moderate = reasonable
- Overton window effect: middle shifts as extremes shift
- Splitting the difference: mathematical compromise on non-mathematical questions
- Balance fallacy interaction: "the truth is somewhere in between"

When golden mean fallacy IS present:
- "The truth is probably somewhere in the middle"
- Splitting the difference between a correct and incorrect position
- Assuming moderation is always more reasonable than strong positions
- "Both extremes are wrong, so the middle must be right"
- Compromising on factual questions (not just values)
- Treating the midpoint as inherently more credible
- "Let's meet in the middle" on questions with objectively correct answers

When middle positions ARE appropriate:
- Genuine value trade-offs where compromise is needed
- Empirical questions where evidence genuinely points to intermediate values
- Negotiations where both parties have legitimate interests
- Complex systems where extreme positions miss important factors
- The middle position is supported by independent evidence
- The question is about degree, not kind

Output JSON with: golden_mean_fallacy_present (bool), severity (none/mild/moderate/severe), dispute (what is being disputed), position_a (one extreme), position_b (other extreme), proposed_middle (what middle ground is suggested), evidence_for_middle (what supports the middle position), independent_basis (does middle have independent justification), correct_position (where does evidence actually point), recommendation (middle_justified/mild_moderation_bias/significant_golden_mean_fallacy/major_false_compromise/evaluate_positions_independently)."""

GOLDEN_MEAN_FALLACY_PROMPT = """Detect golden mean fallacy:

Dispute: {dispute}
Position A: {position_a}
Position B: {position_b}
Proposed resolution: {resolution}
Domain: {domain}
Context: {context}

Is the middle ground being assumed correct simply because it's between two positions? Return ONLY valid JSON."""


class GoldenMeanFallacyService:
    """Detects golden mean fallacy — assuming truth lies between extremes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dispute: str,
        *,
        position_a: str = "",
        position_b: str = "",
        resolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect golden mean fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOLDEN_MEAN_FALLACY_PROMPT.format(
                dispute=dispute,
                position_a=position_a or "Not specified",
                position_b=position_b or "Not specified",
                resolution=resolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GOLDEN_MEAN_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dispute": dispute[:200],
            "golden_mean_fallacy_present": data.get("golden_mean_fallacy_present", False),
            "severity": data.get("severity", ""),
            "position_a": data.get("position_a", ""),
            "position_b": data.get("position_b", ""),
            "proposed_middle": data.get("proposed_middle", ""),
            "evidence_for_middle": data.get("evidence_for_middle", ""),
            "independent_basis": data.get("independent_basis", ""),
            "correct_position": data.get("correct_position", ""),
            "recommendation": data.get("recommendation", ""),
        }

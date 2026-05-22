"""NegativityBiasService — Negativity Bias Detection.

Detects negativity bias — giving more weight to negative
experiences, information, or events than positive ones of equal
magnitude. Baumeister et al. (2001). Bad is stronger than good.
One criticism outweighs ten compliments. One bad experience
ruins an otherwise good day. Losses loom larger than gains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NEGATIVITY_SYSTEM = """You are a negativity bias specialist. Given an evaluation or judgment, assess whether negative information is being overweighted relative to positive information of equal magnitude:

Key concepts (Baumeister et al., 2001):
- Negativity bias: negative events have greater impact than positive events of equal magnitude
- Bad is stronger than good: across domains, negative outweighs positive
- Loss aversion overlap: losses hurt more than equivalent gains feel good
- Negativity dominance: negative information dominates mixed evaluations
- Positive-negative asymmetry: it takes multiple positives to overcome one negative
- Negativity in impression formation: one bad trait ruins an otherwise good impression

When negativity bias IS present:
- One negative review outweighing many positive ones
- A single failure overshadowing a track record of success
- Focusing on what went wrong while ignoring what went right
- Risk assessment dominated by worst-case scenarios
- "But what about..." focusing on the one negative in a sea of positives
- Disproportionate emotional response to negative vs. positive events

When negative focus IS appropriate:
- The negative information is genuinely more diagnostic
- Safety-critical domains where negatives must be weighted heavily
- The negative represents a genuine pattern, not an outlier
- Asymmetric consequences make negative outcomes more important
- The positive information is less reliable or less relevant

Output JSON with: negativity_bias_present (bool), severity (none/mild/moderate/severe), evaluation (what is being evaluated), negative_information (what negative info is being overweighted), positive_information (what positive info is being underweighted), weight_ratio (how much more weight is given to negative?), asymmetric_impact (bool — is one negative outweighing many positives?), domain_appropriateness (is negative focus appropriate for this domain?), emotional_vs_rational (is the weighting emotional or calculated?), base_rate_of_negative (how common is the negative outcome?), overall_balance (what would a balanced assessment look like?), recommendation (negative_focus_appropriate/mild_negativity_bias/significant_overweighting/major_negativity_bias/rebalance_assessment)."""

NEGATIVITY_PROMPT = """Detect negativity bias:

Evaluation: {evaluation}
Negative factors: {negative}
Positive factors: {positive}
Weighting: {weighting}
Domain: {domain}
Context: {context}

Is negative information being overweighted relative to positive? Return ONLY valid JSON."""


class NegativityBiasService:
    """Detects negativity bias — overweighting negative information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        negative: str = "",
        positive: str = "",
        weighting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect negativity bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NEGATIVITY_PROMPT.format(
                evaluation=evaluation,
                negative=negative or "Not specified",
                positive=positive or "Not specified",
                weighting=weighting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NEGATIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "negativity_bias_present": data.get("negativity_bias_present", False),
            "severity": data.get("severity", ""),
            "negative_information": data.get("negative_information", ""),
            "positive_information": data.get("positive_information", ""),
            "weight_ratio": data.get("weight_ratio", ""),
            "asymmetric_impact": data.get("asymmetric_impact", False),
            "domain_appropriateness": data.get("domain_appropriateness", ""),
            "emotional_vs_rational": data.get("emotional_vs_rational", ""),
            "base_rate_of_negative": data.get("base_rate_of_negative", ""),
            "overall_balance": data.get("overall_balance", ""),
            "recommendation": data.get("recommendation", ""),
        }

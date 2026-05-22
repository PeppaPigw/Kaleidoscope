"""ZeroSumThinkingService — Zero-Sum Thinking Detection.

Detects zero-sum thinking — incorrectly assuming that one party's
gain must come at another's expense. Many situations are positive-sum
(trade, cooperation, innovation) or negative-sum (war, litigation,
arms races), but people default to zero-sum framing. This distorts
negotiation, policy, and interpersonal relationships.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ZERO_SUM_SYSTEM = """You are a zero-sum thinking specialist. Given a situation, assess whether zero-sum framing is accurate or distorting:

Key concepts:
- Zero-sum: one party's gain equals another's loss (fixed pie)
- Positive-sum: total value can increase (growing pie, trade, cooperation)
- Negative-sum: total value decreases (war, arms races, destructive competition)
- Variable-sum: the game structure depends on choices made
- Fixed-pie bias: assuming the pie is fixed when it could grow
- Win-win blindness: failing to see mutual benefit opportunities
- Competitive framing: treating cooperation opportunities as competitions

When zero-sum IS accurate:
- Truly fixed resources (one parking spot, one job opening)
- Pure redistribution (tax policy, inheritance)
- Competitive selection (only one winner)

When zero-sum is WRONG:
- Trade (both parties benefit or they wouldn't trade)
- Innovation (creates new value)
- Cooperation (joint surplus exceeds individual efforts)
- Knowledge sharing (non-rivalrous goods)

Output JSON with: zero_sum_thinking_present (bool), severity (none/mild/moderate/severe), actual_game_type (zero_sum/positive_sum/negative_sum/variable_sum/mixed), perceived_game_type (what the actors think it is), framing_error (what's wrong with the zero-sum assumption), fixed_pie_assumption (bool — is a growing pie being treated as fixed?), value_creation_possible (what mutual gains are being missed), competitive_framing (bool — is cooperation being treated as competition?), who_benefits_from_zero_sum_frame (who gains from others seeing it as zero-sum), negotiation_impact (how zero-sum thinking affects negotiation), policy_impact (how it affects policy choices), positive_sum_opportunities (what win-win options exist), negative_sum_risk (could the situation become negative-sum through conflict?), reframing_suggestion (how to shift from zero-sum to positive-sum thinking), historical_examples (similar situations that were reframed successfully), recommendation (correctly_zero_sum/mild_fixed_pie_bias/significant_zero_sum_error/major_value_creation_missed/reframe_urgently)."""

ZERO_SUM_PROMPT = """Detect zero-sum thinking:

Situation: {situation}
Parties involved: {parties}
Resources/stakes: {resources}
Current framing: {framing}
Domain: {domain}
Context: {context}

Is zero-sum thinking distorting this situation? Return ONLY valid JSON."""


class ZeroSumThinkingService:
    """Detects zero-sum thinking — fixed-pie bias in variable-sum situations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        parties: str = "",
        resources: str = "",
        framing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect zero-sum thinking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ZERO_SUM_PROMPT.format(
                situation=situation,
                parties=parties or "Not specified",
                resources=resources or "Not specified",
                framing=framing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ZERO_SUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "zero_sum_thinking_present": data.get("zero_sum_thinking_present", False),
            "severity": data.get("severity", ""),
            "actual_game_type": data.get("actual_game_type", ""),
            "perceived_game_type": data.get("perceived_game_type", ""),
            "framing_error": data.get("framing_error", ""),
            "fixed_pie_assumption": data.get("fixed_pie_assumption", False),
            "value_creation_possible": data.get("value_creation_possible", ""),
            "competitive_framing": data.get("competitive_framing", False),
            "who_benefits_from_zero_sum_frame": data.get("who_benefits_from_zero_sum_frame", ""),
            "negotiation_impact": data.get("negotiation_impact", ""),
            "policy_impact": data.get("policy_impact", ""),
            "positive_sum_opportunities": data.get("positive_sum_opportunities", ""),
            "negative_sum_risk": data.get("negative_sum_risk", ""),
            "reframing_suggestion": data.get("reframing_suggestion", ""),
            "historical_examples": data.get("historical_examples", []),
            "recommendation": data.get("recommendation", ""),
        }

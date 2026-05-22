"""ZeroSumBiasService — Zero-Sum Bias Detection.

Detects zero-sum bias — incorrectly assuming that situations
are zero-sum (one party's gain must be another's loss) when
they are actually positive-sum or variable-sum. Meegan (2010).
"If they win, I lose." Prevents collaboration, negotiation,
and recognition of mutual benefit opportunities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ZERO_SUM_SYSTEM = """You are a zero-sum bias specialist. Given a situation being framed as zero-sum, assess whether the framing is accurate or whether mutual gains are possible:

Key concepts (Meegan, 2010):
- Zero-sum bias: assuming one party's gain requires another's loss
- Fixed pie assumption: believing resources/value cannot be expanded
- Win-lose framing: seeing all interactions as competitive
- Positive-sum blindness: missing opportunities for mutual benefit
- Negotiation myopia: failing to find integrative solutions
- Competitive framing: treating collaboration opportunities as competitions
- Value creation vs. value claiming: only seeing the claiming dimension

When zero-sum bias IS present:
- "If they get more, I get less" in expandable situations
- Opposing others' gains even when they don't reduce own gains
- Failing to see collaboration opportunities
- Fixed-pie assumptions in negotiations with integrative potential
- "There's only so much to go around" when value can be created
- Opposing immigration/trade/growth based on zero-sum assumptions

When the situation IS genuinely zero-sum:
- Resources are truly fixed and cannot be expanded
- One party's gain demonstrably reduces another's
- The situation is a pure distribution problem
- No integrative solutions exist (verified, not assumed)
- The competitive framing matches the actual structure

Output JSON with: zero_sum_bias_present (bool), severity (none/mild/moderate/severe), situation (what situation is being framed as zero-sum), framing (how is it being framed), actual_structure (is it actually zero-sum, positive-sum, or variable-sum?), mutual_gains_possible (what mutual gains might exist?), value_creation_opportunity (can value be created rather than just distributed?), competitive_assumption (what competitive assumption is being made?), collaboration_blocked (what collaboration is being prevented?), recommendation (genuinely_zero_sum/mild_fixed_pie/significant_zero_sum_bias/major_positive_sum_blindness/explore_mutual_gains)."""

ZERO_SUM_PROMPT = """Detect zero-sum bias:

Situation: {situation}
Framing: {framing}
Parties: {parties}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is this situation incorrectly being framed as zero-sum? Return ONLY valid JSON."""


class ZeroSumBiasService:
    """Detects zero-sum bias — incorrectly assuming win-lose when mutual gains exist."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        framing: str = "",
        parties: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect zero-sum bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ZERO_SUM_PROMPT.format(
                situation=situation,
                framing=framing or "Not specified",
                parties=parties or "Not specified",
                alternatives=alternatives or "Not specified",
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
            "zero_sum_bias_present": data.get("zero_sum_bias_present", False),
            "severity": data.get("severity", ""),
            "actual_structure": data.get("actual_structure", ""),
            "mutual_gains_possible": data.get("mutual_gains_possible", ""),
            "value_creation_opportunity": data.get("value_creation_opportunity", ""),
            "competitive_assumption": data.get("competitive_assumption", ""),
            "collaboration_blocked": data.get("collaboration_blocked", ""),
            "recommendation": data.get("recommendation", ""),
        }

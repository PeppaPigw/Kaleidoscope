"""TemporalMyopiaService — Temporal Myopia Detection.

Detects temporal myopia — systematically overweighting near-term
consequences while underweighting long-term ones beyond what
rational discounting would justify. Unlike present bias (which
is about immediate gratification), temporal myopia is about
the cognitive inability to vividly represent distant futures,
making them feel less real and less important.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_MYOPIA_SYSTEM = """You are a temporal myopia specialist. Given a decision or evaluation, assess whether near-term consequences are being systematically overweighted relative to long-term ones:

Key concepts:
- Temporal myopia: inability to vividly represent distant futures
- Near-term concreteness: immediate consequences feel more real
- Future abstractness: distant outcomes feel hypothetical
- Construal level theory: distant events represented abstractly
- Temporal discounting beyond rationality: excessive devaluation of future
- Short-termism: organizational bias toward immediate results
- Intergenerational myopia: discounting future generations' welfare

When temporal myopia IS present:
- Choosing options with clear near-term benefits despite severe long-term costs
- "We'll deal with that later" for predictable future problems
- Quarterly thinking overriding strategic planning
- Technical debt accumulation without accounting for future cost
- Ignoring slow-moving risks (climate, demographic shifts, skill decay)
- "The future is uncertain anyway" as excuse to ignore likely outcomes
- Vivid near-term costs blocking investment with diffuse long-term benefits

When near-term focus IS appropriate:
- Genuine uncertainty makes long-term prediction unreliable
- Survival constraints require immediate action
- The discount rate is rationally justified by opportunity cost
- Near-term actions create optionality for future decisions
- The long-term consequences are genuinely speculative

Output JSON with: temporal_myopia_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), near_term_weight (how near-term is being weighted), long_term_weight (how long-term is being weighted), time_horizon (what time horizons are involved), concreteness_gap (difference in vividness between near and far), rational_discount (what would rational discounting look like), recommendation (time_weighting_appropriate/mild_near_term_bias/significant_temporal_myopia/major_short_termism/extend_time_horizon)."""

TEMPORAL_MYOPIA_PROMPT = """Detect temporal myopia:

Decision: {decision}
Near-term factors: {near_term}
Long-term factors: {long_term}
Time horizon: {horizon}
Domain: {domain}
Context: {context}

Are near-term consequences being systematically overweighted relative to long-term ones? Return ONLY valid JSON."""


class TemporalMyopiaService:
    """Detects temporal myopia — overweighting near-term over long-term consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        near_term: str = "",
        long_term: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect temporal myopia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_MYOPIA_PROMPT.format(
                decision=decision,
                near_term=near_term or "Not specified",
                long_term=long_term or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_MYOPIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "temporal_myopia_present": data.get("temporal_myopia_present", False),
            "severity": data.get("severity", ""),
            "near_term_weight": data.get("near_term_weight", ""),
            "long_term_weight": data.get("long_term_weight", ""),
            "time_horizon": data.get("time_horizon", ""),
            "concreteness_gap": data.get("concreteness_gap", ""),
            "rational_discount": data.get("rational_discount", ""),
            "recommendation": data.get("recommendation", ""),
        }

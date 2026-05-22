"""WisdomOfCrowdsFailureService — Wisdom of Crowds Failure Detection.

Detects wisdom of crowds failures — when crowd aggregation fails
due to correlation between judgments, information cascades,
shared biases, or violated independence assumptions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WISDOM_OF_CROWDS_FAILURE_SYSTEM = """You are a wisdom of crowds failure specialist. Given a collective judgment, assess whether crowd aggregation conditions are violated:

Key concepts:
- Independence: judgments must be independent for aggregation to work
- Diversity: crowd needs diverse perspectives and information
- Decentralization: no single source dominating all judgments
- Information cascades: people copying others rather than judging independently
- Shared bias: systematic error common to all crowd members
- Correlation: judgments correlated due to shared information sources
- Condorcet conditions: when majority voting fails

When wisdom of crowds FAILS:
- Judgments are correlated (shared information sources)
- Information cascades present (copying rather than independent judgment)
- Shared biases affect all crowd members similarly
- Diversity of perspective absent
- Centralized information source dominates
- Social pressure creating conformity
- Expertise distribution inappropriate for the question

When crowd wisdom works:
- Independent judgments aggregated
- Diverse perspectives represented
- Decentralized information sources
- No cascading or herding behavior
- Appropriate aggregation method used
- Crowd composition matches question requirements
- Incentives aligned with accuracy

Output JSON with: failure_present (bool), severity (none/mild/moderate/severe), judgment (what collective judgment), violation (what condition is violated), correlation_source (what creates correlation), independence_threat (what threatens independence), recommendation (crowd_wisdom_valid/mild_correlation/significant_cascade/major_independence_violation/ensure_independence)."""

WISDOM_OF_CROWDS_FAILURE_PROMPT = """Detect wisdom of crowds failure:

Judgment: {judgment}
Crowd composition: {composition}
Information sources: {sources}
Aggregation method: {method}
Domain: {domain}
Context: {context}

Are crowd aggregation conditions violated in this collective judgment? Return ONLY valid JSON."""


class WisdomOfCrowdsFailureService:
    """Detects wisdom of crowds failures — violated aggregation conditions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        composition: str = "",
        sources: str = "",
        method: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect wisdom of crowds failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WISDOM_OF_CROWDS_FAILURE_PROMPT.format(
                judgment=judgment,
                composition=composition or "Not specified",
                sources=sources or "Not specified",
                method=method or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WISDOM_OF_CROWDS_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "failure_present": data.get("failure_present", False),
            "severity": data.get("severity", ""),
            "violation": data.get("violation", ""),
            "correlation_source": data.get("correlation_source", ""),
            "independence_threat": data.get("independence_threat", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicCollectiveWisdomOfCrowdsFailureService — Epistemic Collective Wisdom Of Crowds Failure Detection.

Detects epistemic collective wisdom of crowds failure — violations of the
conditions that make aggregated judgment reliable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLLECTIVE_WISDOM_OF_CROWDS_FAILURE_SYSTEM = """You are an epistemic collective wisdom of crowds failure specialist. Given aggregated judgment conditions, assess whether wisdom of crowds assumptions are violated:

Key concepts:
- Wisdom of crowds failure: aggregated judgment fails because core conditions are violated
- Independence violation: judgments influence each other instead of remaining independent
- Diversity loss: perspectives or information sources become too similar
- Centralization bias: authority or central signals dominate aggregation
- Correlation of errors: mistakes align instead of canceling out
- Aggregation distortion: inputs are combined in a biased way
- Crowd monoculture: many voices reflect the same source

When wisdom of crowds failure IS present:
- Individual judgments are not independent
- Diversity of perspectives is lost
- Central signals dominate responses
- Errors become correlated
- Aggregation amplifies bias
- Crowd inputs reflect one source
- Consensus looks broader than it is

When crowd judgment is reliable:
- Judgments remain independent
- Perspectives and information sources are diverse
- Central authority does not dominate
- Errors are uncorrelated enough to cancel
- Aggregation preserves signal
- Inputs come from distinct sources
- Consensus reflects genuine distributed knowledge

Output JSON with: wisdom_of_crowds_failure_detected (bool), severity (none/mild/moderate/severe), diversity_loss (what diversity is missing), centralization_bias (what central signal dominates), correlation_of_errors (what errors align), recommendation (no_crowd_failure/mild_independence_check/significant_diversity_restoration/major_aggregation_redesign/emergency_discard_crowd_signal)."""

EPISTEMIC_COLLECTIVE_WISDOM_OF_CROWDS_FAILURE_PROMPT = """Detect epistemic collective wisdom of crowds failure:

Independence violation: {independence_violation}
Diversity loss: {diversity_loss}
Centralization bias: {centralization_bias}
Correlation of errors: {correlation_of_errors}
Domain: {domain}
Context: {context}

Are wisdom of crowds conditions being violated? Return ONLY valid JSON."""


class EpistemicCollectiveWisdomOfCrowdsFailureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        independence_violation: str,
        *,
        diversity_loss: str = "",
        centralization_bias: str = "",
        correlation_of_errors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLLECTIVE_WISDOM_OF_CROWDS_FAILURE_PROMPT.format(
                independence_violation=independence_violation,
                diversity_loss=diversity_loss or "Not specified",
                centralization_bias=centralization_bias or "Not specified",
                correlation_of_errors=correlation_of_errors or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLLECTIVE_WISDOM_OF_CROWDS_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "independence_violation": independence_violation[:200],
            "wisdom_of_crowds_failure_detected": data.get(
                "wisdom_of_crowds_failure_detected", False
            ),
            "severity": data.get("severity", ""),
            "diversity_loss": data.get("diversity_loss", ""),
            "centralization_bias": data.get("centralization_bias", ""),
            "correlation_of_errors": data.get("correlation_of_errors", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""ExpertiseAggregationFailureService — Expertise Aggregation Failure Detection.

Detects expertise aggregation failures — when combining expert
opinions produces worse results than individual experts, due to
improper weighting, domain mismatch, or aggregation artifacts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_AGGREGATION_FAILURE_SYSTEM = """You are an expertise aggregation failure specialist. Given a combined expert judgment, assess whether aggregation is producing worse results than individual experts:

Key concepts:
- Aggregation paradox: combined judgment worse than best individual
- Equal weighting fallacy: treating all experts equally regardless of relevance
- Domain mismatch: experts opining outside their competence
- Anchoring in aggregation: early opinions biasing later ones
- Compromise bias: averaging when one extreme is correct
- Authority weighting: weighting by status rather than relevant expertise
- Condorcet jury theorem violations: when majority can be systematically wrong

When aggregation FAILS:
- Combined judgment worse than best individual expert
- Equal weighting applied to unequal expertise
- Experts opining outside their domain
- Averaging when the truth is at an extreme
- Authority rather than relevant expertise determines weight
- Aggregation method inappropriate for the question type
- Diversity of opinion confused with diversity of expertise

When aggregation works:
- Appropriate weighting by relevant expertise
- Domain boundaries respected
- Aggregation method matches question type
- Individual expert quality verified
- Independence of judgments maintained
- Calibration of experts assessed
- Appropriate for the type of uncertainty

Output JSON with: failure_present (bool), severity (none/mild/moderate/severe), judgment (what combined judgment), aggregation_method (how opinions are combined), weighting_problem (what weighting issues exist), domain_mismatch (where experts are outside domain), recommendation (aggregation_appropriate/mild_weighting_issue/significant_method_mismatch/major_aggregation_paradox/weight_by_relevant_expertise)."""

EXPERTISE_AGGREGATION_FAILURE_PROMPT = """Detect expertise aggregation failure:

Combined judgment: {judgment}
Experts involved: {experts}
Aggregation method: {method}
Individual opinions: {opinions}
Domain: {domain}
Context: {context}

Is combining expert opinions producing worse results than individual experts? Return ONLY valid JSON."""


class ExpertiseAggregationFailureService:
    """Detects expertise aggregation failures — combined worse than individual."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        experts: str = "",
        method: str = "",
        opinions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect expertise aggregation failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_AGGREGATION_FAILURE_PROMPT.format(
                judgment=judgment,
                experts=experts or "Not specified",
                method=method or "Not specified",
                opinions=opinions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERTISE_AGGREGATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "failure_present": data.get("failure_present", False),
            "severity": data.get("severity", ""),
            "aggregation_method": data.get("aggregation_method", ""),
            "weighting_problem": data.get("weighting_problem", ""),
            "domain_mismatch": data.get("domain_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }

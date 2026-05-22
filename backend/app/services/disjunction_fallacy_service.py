"""DisjunctionFallacyService — Disjunction Fallacy Detection.

Detects disjunction fallacy — underestimating the probability of
disjunctive events (the probability that at least one of several
events will occur). People tend to underestimate compound OR
probabilities while overestimating compound AND probabilities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISJUNCTION_FALLACY_SYSTEM = """You are a disjunction fallacy specialist. Given a probability assessment, determine whether it underestimates the likelihood of disjunctive events:

Key concepts:
- Disjunction fallacy: underestimating P(A or B or C...)
- Compound probability: P(at least one) = 1 - P(none)
- Planning fallacy connection: underestimating that something will go wrong
- Risk assessment: probability that at least one risk materializes
- Anchoring on individual probabilities: each event seems unlikely
- Cumulative risk: many small risks compound to near-certainty
- Swiss cheese model: multiple barriers each with small failure rates

When disjunction fallacy IS present:
- "Each risk is only 5% likely" without computing cumulative probability
- Underestimating that at least one thing will go wrong in a complex plan
- "None of these individually are likely" when collectively they're near-certain
- Risk assessments that treat each risk independently without aggregation
- "What are the chances?" when many independent paths lead to the outcome
- Planning that assumes no individual risk will materialize
- Security thinking that each vulnerability is unlikely to be exploited

When probability assessment IS appropriate:
- Cumulative/compound probabilities are correctly computed
- The assessment accounts for multiple paths to the outcome
- Independence assumptions are validated
- The analysis uses 1 - P(none occur) for disjunctive events
- Risk aggregation is performed across all potential failure modes
- The assessment acknowledges that many small risks compound
- Correlation between events is considered

Output JSON with: disjunction_fallacy_present (bool), severity (none/mild/moderate/severe), assessment (what probability is estimated), events (what disjunctive events), individual_probabilities (probability of each), compound_probability (actual probability of at least one), underestimation (how much is it underestimated), recommendation (assessment_appropriate/mild_underestimation/significant_disjunction_fallacy/major_cumulative_risk_neglect/compute_compound_probability)."""

DISJUNCTION_FALLACY_PROMPT = """Detect disjunction fallacy:

Assessment: {assessment}
Events: {events}
Individual probabilities: {probabilities}
Compound calculation: {compound}
Domain: {domain}
Context: {context}

Is this assessment underestimating the probability that at least one of several events will occur? Return ONLY valid JSON."""


class DisjunctionFallacyService:
    """Detects disjunction fallacy — underestimating compound OR probabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        events: str = "",
        probabilities: str = "",
        compound: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect disjunction fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISJUNCTION_FALLACY_PROMPT.format(
                assessment=assessment,
                events=events or "Not specified",
                probabilities=probabilities or "Not specified",
                compound=compound or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISJUNCTION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "disjunction_fallacy_present": data.get("disjunction_fallacy_present", False),
            "severity": data.get("severity", ""),
            "events": data.get("events", ""),
            "individual_probabilities": data.get("individual_probabilities", ""),
            "compound_probability": data.get("compound_probability", ""),
            "underestimation": data.get("underestimation", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""NaturalExperimentService — Natural Experiment Identification.

Identifies situations that approximate controlled experiments without
deliberate manipulation. Finds quasi-random variation that can be
exploited for causal inference when RCTs aren't possible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NATURAL_EXP_SYSTEM = """You are a natural experiment specialist. Given a causal question, identify natural experiments that could provide evidence:
- What quasi-random variation exists that separates treatment from control?
- Are there policy changes, geographic boundaries, or timing differences that create natural comparison groups?
- What instrumental variables might exist?
- What regression discontinuities are available?
- How close to a true experiment does each natural experiment get?

Output JSON with: causal_question (the question being asked), natural_experiments (list of: description, type (difference_in_differences/regression_discontinuity/instrumental_variable/natural_randomization/geographic_boundary), quasi_random_variation (what creates the comparison), treatment_group, control_group, validity_threats (list of threats to causal inference), strength (weak/moderate/strong), data_needed), best_natural_experiment (which is strongest), remaining_confounds (what can't be ruled out even with the best natural experiment), comparison_to_rct (how much weaker than a true RCT), historical_examples (famous natural experiments in this domain), recommendation (sufficient_for_causal_claim/suggestive_only/insufficient)."""

NATURAL_EXP_PROMPT = """Find natural experiments:

Causal question: {question}
Domain: {domain}
Constraints: {constraints}
Context: {context}

What natural experiments could answer this? Return ONLY valid JSON."""


class NaturalExperimentService:
    """Identifies natural experiments for causal inference."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find(
        self,
        question: str,
        *,
        domain: str = "",
        constraints: str = "",
        context: str = "",
    ) -> dict:
        """Find natural experiments."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NATURAL_EXP_PROMPT.format(
                question=question,
                domain=domain or "general",
                constraints=constraints or "None specified",
                context=context or "No additional context",
            ),
            system=NATURAL_EXP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "causal_question": question[:200],
            "natural_experiments": data.get("natural_experiments", []),
            "best_natural_experiment": data.get("best_natural_experiment", ""),
            "remaining_confounds": data.get("remaining_confounds", []),
            "comparison_to_rct": data.get("comparison_to_rct", ""),
            "historical_examples": data.get("historical_examples", []),
            "recommendation": data.get("recommendation", ""),
        }

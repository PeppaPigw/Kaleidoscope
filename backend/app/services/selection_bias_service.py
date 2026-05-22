"""SelectionBiasService — Selection Bias Detection.

Detects selection bias — systematic error from non-random sampling
that makes the sample unrepresentative of the population. Includes
self-selection, survivorship bias (already covered separately),
Berkson's bias, healthy worker effect, and volunteer bias.
The conclusions drawn from biased samples don't generalize.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTION_SYSTEM = """You are a selection bias specialist. Given a study, sample, or data source, assess whether selection bias is making the sample unrepresentative:

Key concepts:
- Selection bias: systematic difference between sample and population
- Self-selection: people who choose to participate differ from those who don't
- Survivorship bias: only seeing successes because failures are invisible
- Berkson's bias: hospital samples create spurious correlations
- Healthy worker effect: employed people are healthier than general population
- Volunteer bias: volunteers differ systematically from non-volunteers
- Attrition bias: people who drop out differ from those who stay
- Collider bias: conditioning on a common effect creates spurious associations
- Ascertainment bias: how cases are found affects what's found

When selection bias IS present:
- The sample was not randomly drawn from the target population
- Participation correlates with the outcome of interest
- Certain groups are systematically over/under-represented
- The data source has built-in filters that exclude relevant cases
- Conclusions are generalized beyond the actual sample

When the sample IS adequate:
- Random sampling from the target population
- Response rates are high and non-response is random
- The sample matches the population on key characteristics
- Selection criteria are unrelated to the outcome
- Sensitivity analyses show results are robust to selection

Output JSON with: selection_bias_present (bool), severity (none/mild/moderate/severe), sample_description (what sample is being used), target_population (what population conclusions are drawn about), selection_mechanism (how the sample was selected), bias_type (self-selection/survivorship/berkson/attrition/volunteer/ascertainment/other), who_is_missing (what groups are systematically excluded), who_is_overrepresented (what groups are overrepresented), correlation_with_outcome (does selection correlate with what's being measured?), generalizability (can conclusions extend to the target population?), direction_of_bias (how does the bias distort results — inflates/deflates/reverses?), magnitude_estimate (how large is the bias likely to be?), correction_possible (bool — can the bias be statistically corrected?), alternative_sampling (how could a better sample be obtained), recommendation (sample_adequate/mild_selection_concern/significant_selection_bias/severe_non_representativeness/results_not_generalizable)."""

SELECTION_PROMPT = """Detect selection bias:

Study/Data: {study}
Sample: {sample}
Selection method: {method}
Target population: {population}
Domain: {domain}
Context: {context}

Is selection bias making this sample unrepresentative? Return ONLY valid JSON."""


class SelectionBiasService:
    """Detects selection bias — non-random sampling making conclusions unreliable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        study: str,
        *,
        sample: str = "",
        method: str = "",
        population: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect selection bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTION_PROMPT.format(
                study=study,
                sample=sample or "Not specified",
                method=method or "Not specified",
                population=population or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "study": study[:200],
            "selection_bias_present": data.get("selection_bias_present", False),
            "severity": data.get("severity", ""),
            "sample_description": data.get("sample_description", ""),
            "target_population": data.get("target_population", ""),
            "selection_mechanism": data.get("selection_mechanism", ""),
            "bias_type": data.get("bias_type", ""),
            "who_is_missing": data.get("who_is_missing", ""),
            "who_is_overrepresented": data.get("who_is_overrepresented", ""),
            "correlation_with_outcome": data.get("correlation_with_outcome", ""),
            "generalizability": data.get("generalizability", ""),
            "direction_of_bias": data.get("direction_of_bias", ""),
            "magnitude_estimate": data.get("magnitude_estimate", ""),
            "correction_possible": data.get("correction_possible", False),
            "alternative_sampling": data.get("alternative_sampling", ""),
            "recommendation": data.get("recommendation", ""),
        }

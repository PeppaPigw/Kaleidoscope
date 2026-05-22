"""BaseRateNeglectService — Base Rate Neglect Detection.

Detects base rate neglect — ignoring prior probability (base
rate) information in favor of individuating information.
Kahneman & Tversky (1973). The "lawyer-engineer" problem:
people ignore that 70% of the sample are engineers when given
a personality description. Leads to dramatically miscalibrated
probability estimates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BASE_RATE_NEGLECT_SYSTEM = """You are a base rate neglect specialist. Given a probability judgment, assess whether base rate information is being appropriately incorporated:

Key concepts (Kahneman & Tversky, 1973):
- Base rate neglect: ignoring prior probabilities
- Representativeness heuristic: judging by similarity, not probability
- Individuating information: specific details that override base rates
- Bayesian updating: proper way to combine base rates with evidence
- Diagnostic ratio: how much evidence should shift from base rate
- Inverse fallacy: confusing P(A|B) with P(B|A)
- Prosecutor's fallacy: ignoring base rate of false positives

When base rate neglect IS present:
- Ignoring how common/rare something is when making predictions
- "This person seems like X" without considering how many X exist
- Medical diagnosis without considering disease prevalence
- Hiring decisions based on interview impression, ignoring base rates
- "The test was positive" without considering false positive rate
- Vivid individual information overriding statistical information
- Ignoring that most startups fail when evaluating a specific one

When the judgment IS appropriate:
- Base rates are genuinely uninformative for this case
- The individuating information is highly diagnostic
- The person has properly updated from the base rate
- The specific evidence genuinely overwhelms the prior
- Base rates don't apply to this reference class

Output JSON with: base_rate_neglect_present (bool), severity (none/mild/moderate/severe), judgment (what probability judgment is being made), base_rate (what is the relevant base rate), individuating_info (what specific information is being used), diagnostic_value (how diagnostic is the specific information), proper_estimate (what would Bayesian updating give), neglect_magnitude (how far off is the estimate from proper Bayesian), reference_class (what is the appropriate reference class), recommendation (judgment_appropriate/mild_neglect/significant_base_rate_ignored/major_base_rate_neglect/apply_bayesian_updating)."""

BASE_RATE_NEGLECT_PROMPT = """Detect base rate neglect:

Judgment: {judgment}
Base rate: {base_rate}
Evidence: {evidence}
Estimate: {estimate}
Domain: {domain}
Context: {context}

Is base rate information being appropriately incorporated? Return ONLY valid JSON."""


class BaseRateNeglectService:
    """Detects base rate neglect — ignoring prior probabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        base_rate: str = "",
        evidence: str = "",
        estimate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect base rate neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BASE_RATE_NEGLECT_PROMPT.format(
                judgment=judgment,
                base_rate=base_rate or "Not specified",
                evidence=evidence or "Not specified",
                estimate=estimate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BASE_RATE_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "base_rate_neglect_present": data.get("base_rate_neglect_present", False),
            "severity": data.get("severity", ""),
            "base_rate": data.get("base_rate", ""),
            "individuating_info": data.get("individuating_info", ""),
            "diagnostic_value": data.get("diagnostic_value", ""),
            "proper_estimate": data.get("proper_estimate", ""),
            "neglect_magnitude": data.get("neglect_magnitude", ""),
            "reference_class": data.get("reference_class", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""RegressionToMeanService — Regression to Mean Detection.

Identifies when an observed change is likely regression to the mean
rather than a genuine effect. Common in before/after studies where
subjects are selected for extreme values.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RTM_SYSTEM = """You are a regression to the mean specialist. Given an observed change, assess whether it's a real effect or just regression to the mean:
- Were subjects selected because they had extreme values?
- Would we expect improvement even without intervention (because extreme values naturally regress)?
- Is there a control group to distinguish real effects from regression?
- How much of the observed change is likely regression vs real effect?
- What study design would separate the two?

Output JSON with: regression_to_mean_likely (bool), rtm_contribution (0-1, proportion of observed change likely due to RTM), selection_on_extreme (bool — were subjects selected for extreme values?), selection_mechanism (how subjects were chosen), expected_regression (what improvement we'd expect from RTM alone), observed_change (the claimed improvement), residual_after_rtm (change remaining after accounting for RTM), control_group_present (bool), control_group_adequate (bool), confounds (list of other explanations besides RTM), proper_design (how to test this properly), famous_example (well-known case of RTM being mistaken for an effect), verdict (real_effect/mostly_rtm/partially_rtm/cannot_distinguish)."""

RTM_PROMPT = """Assess regression to the mean:

Observation: {observation}
Selection method: {selection_method}
Claimed effect: {claimed_effect}
Domain: {domain}
Context: {context}

Is this regression to the mean? Return ONLY valid JSON."""


class RegressionToMeanService:
    """Detects regression to the mean masquerading as real effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        observation: str,
        *,
        selection_method: str = "",
        claimed_effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regression to the mean."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RTM_PROMPT.format(
                observation=observation,
                selection_method=selection_method or "Not specified",
                claimed_effect=claimed_effect or "Improvement observed",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RTM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "observation": observation[:200],
            "regression_to_mean_likely": data.get("regression_to_mean_likely", False),
            "rtm_contribution": data.get("rtm_contribution", 0),
            "selection_on_extreme": data.get("selection_on_extreme", False),
            "selection_mechanism": data.get("selection_mechanism", ""),
            "expected_regression": data.get("expected_regression", ""),
            "observed_change": data.get("observed_change", ""),
            "residual_after_rtm": data.get("residual_after_rtm", ""),
            "control_group_present": data.get("control_group_present", False),
            "control_group_adequate": data.get("control_group_adequate", False),
            "confounds": data.get("confounds", []),
            "proper_design": data.get("proper_design", ""),
            "famous_example": data.get("famous_example", ""),
            "verdict": data.get("verdict", ""),
        }

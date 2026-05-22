"""RegressionMeanNeglectService — Regression to Mean Neglect Detection.

Detects regression to mean neglect — failing to account for the
statistical phenomenon where extreme observations tend to be followed
by less extreme ones, leading to false causal attributions for what
is actually a statistical artifact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REGRESSION_MEAN_SYSTEM = """You are a regression to mean specialist. Given a causal claim about sequential observations, assess whether it neglects regression to the mean:

Key concepts:
- Regression to mean: extreme values tend to be followed by less extreme ones
- Statistical artifact: not caused by any intervention
- Galton's insight: extreme parents have less extreme children (on average)
- False attribution: crediting an intervention for natural regression
- Sports Illustrated jinx: extreme performance followed by regression
- Punishment/reward illusion: regression mistaken for effects of feedback
- Measurement error: contributes to apparent regression

When regression neglect IS present:
- Crediting an intervention for improvement after extreme poor performance
- "The treatment worked" when improvement was expected statistically
- Blaming a change for decline after extreme good performance
- "Things got worse after X" when regression was expected
- Ignoring that extreme observations are partly due to luck/noise
- Attributing regression to whatever happened between measurements
- "The crackdown worked" after a spike in crime (which would regress anyway)

When causal attribution IS appropriate:
- The effect persists beyond what regression would predict
- Control groups show the effect is beyond regression
- The mechanism is well-understood and independently validated
- The change is larger than expected from regression alone
- Multiple independent measurements confirm the effect
- The baseline was stable (not an extreme observation)
- Proper experimental design controls for regression

Output JSON with: regression_neglect_present (bool), severity (none/mild/moderate/severe), observation (what is observed), attribution (what cause is attributed), baseline (was the baseline extreme), expected_regression (what regression would predict), actual_change (what change occurred), recommendation (attribution_appropriate/mild_regression_neglect/significant_false_attribution/major_regression_artifact/control_for_regression)."""

REGRESSION_MEAN_PROMPT = """Detect regression to mean neglect:

Observation: {observation}
Attribution: {attribution}
Baseline: {baseline}
Intervention: {intervention}
Domain: {domain}
Context: {context}

Is this causal attribution actually just regression to the mean? Return ONLY valid JSON."""


class RegressionMeanNeglectService:
    """Detects regression to mean neglect — false causal attribution for statistical regression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        observation: str,
        *,
        attribution: str = "",
        baseline: str = "",
        intervention: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regression to mean neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REGRESSION_MEAN_PROMPT.format(
                observation=observation,
                attribution=attribution or "Not specified",
                baseline=baseline or "Not specified",
                intervention=intervention or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REGRESSION_MEAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "observation": observation[:200],
            "regression_neglect_present": data.get("regression_neglect_present", False),
            "severity": data.get("severity", ""),
            "attribution": data.get("attribution", ""),
            "expected_regression": data.get("expected_regression", ""),
            "actual_change": data.get("actual_change", ""),
            "recommendation": data.get("recommendation", ""),
        }

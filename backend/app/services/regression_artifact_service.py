"""RegressionArtifactService — Regression Artifact Detection.

Detects regression artifacts — mistaking regression to the mean
for a real effect of an intervention, when extreme values
naturally revert toward the average.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REGRESSION_ARTIFACT_SYSTEM = """You are a regression artifact specialist. Given a claimed effect, assess whether it is actually regression to the mean:

Key concepts:
- Regression to the mean: extreme values naturally revert toward average
- Selection on extremes: choosing subjects because they're extreme
- Imperfect correlation: less-than-perfect correlation guarantees regression
- Intervention timing: interventions applied after extreme observations
- Natural variation: random fluctuation creating apparent patterns
- Pre-post design flaw: measuring before and after without control
- Ceiling/floor effects: extreme values having nowhere to go but back

When regression artifact IS present:
- Subjects selected because of extreme scores
- Intervention applied after extreme observation
- No control group to compare against
- Improvement attributed to intervention when regression expected
- Pre-post design without accounting for regression
- Extreme performers "returning to form" called an effect
- Natural variation mistaken for intervention effect

When effect is genuine:
- Control group shows less regression than treatment
- Effect size exceeds expected regression
- Selection not based on extreme scores
- Randomized design controls for regression
- Regression to mean explicitly accounted for
- Effect persists beyond regression period
- Multiple measurement points show sustained change

Output JSON with: artifact_present (bool), severity (none/mild/moderate/severe), claimed_effect (what effect is claimed), selection (how subjects were selected), regression_expected (what regression would predict), control_group (whether control exists), recommendation (genuine_effect/mild_regression_risk/significant_artifact/major_regression_to_mean/add_control_group)."""

REGRESSION_ARTIFACT_PROMPT = """Detect regression artifact:

Claimed effect: {effect}
Selection method: {selection}
Intervention: {intervention}
Control group: {control}
Domain: {domain}
Context: {context}

Is this claimed effect actually regression to the mean? Return ONLY valid JSON."""


class RegressionArtifactService:
    """Detects regression artifacts — regression to mean mistaken for real effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        effect: str,
        *,
        selection: str = "",
        intervention: str = "",
        control: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect regression artifact."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REGRESSION_ARTIFACT_PROMPT.format(
                effect=effect,
                selection=selection or "Not specified",
                intervention=intervention or "Not specified",
                control=control or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REGRESSION_ARTIFACT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "effect": effect[:200],
            "artifact_present": data.get("artifact_present", False),
            "severity": data.get("severity", ""),
            "selection": data.get("selection", ""),
            "regression_expected": data.get("regression_expected", ""),
            "control_group": data.get("control_group", ""),
            "recommendation": data.get("recommendation", ""),
        }

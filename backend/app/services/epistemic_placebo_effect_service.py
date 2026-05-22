"""EpistemicPlaceboEffectService — Epistemic Placebo Effect Detection.

Detects epistemic placebo effect — improvement from belief in treatment
rather than the treatment itself, where expectation drives outcome.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PLACEBO_EFFECT_SYSTEM = """You are an epistemic placebo effect specialist. Given intellectual treatment outcomes, assess whether improvement comes from belief rather than substance:

Key concepts:
- Epistemic placebo effect: improvement from belief rather than treatment
- Expectation bias: outcome shaped by what's expected
- Nocebo: harm from negative expectation
- Conditioning: learned response to treatment ritual
- Regression to mean: natural improvement attributed to treatment
- Active placebo: treatment with side effects but no real mechanism
- Blinding failure: knowing treatment status affecting outcome

When epistemic placebo effect IS present:
- Improvement from belief rather than treatment substance
- Outcome shaped by expectations
- Harm from negative expectations
- Learned response to intellectual rituals
- Natural improvement attributed to intervention
- Treatment with appearance but no mechanism
- Knowledge of treatment status affecting outcome

When genuine treatment effect is present:
- Improvement from actual mechanism
- Outcome independent of expectations
- No nocebo effects
- Response independent of ritual
- Improvement beyond natural regression
- Clear mechanism of action
- Blinding maintained

Output JSON with: placebo_effect_present (bool), severity (none/mild/moderate/severe), expectation_bias (what shaped by belief), nocebo (what negative expectation harm), conditioning (what learned response), regression_to_mean (what natural improvement), recommendation (genuine_effect/mild_placebo/significant_placebo_effect/major_belief_driven_outcome/distinguish_real_from_perceived_improvement)."""

EPISTEMIC_PLACEBO_EFFECT_PROMPT = """Detect epistemic placebo effect:

Expectation bias: {expectation_bias}
Nocebo: {nocebo}
Conditioning: {conditioning}
Regression to mean: {regression_to_mean}
Domain: {domain}
Context: {context}

Is improvement coming from belief in treatment rather than the treatment itself? Return ONLY valid JSON."""


class EpistemicPlaceboEffectService:
    """Detects epistemic placebo effect — belief-driven rather than real improvement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        expectation_bias: str,
        *,
        nocebo: str = "",
        conditioning: str = "",
        regression_to_mean: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic placebo effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PLACEBO_EFFECT_PROMPT.format(
                expectation_bias=expectation_bias,
                nocebo=nocebo or "Not specified",
                conditioning=conditioning or "Not specified",
                regression_to_mean=regression_to_mean or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PLACEBO_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "expectation_bias": expectation_bias[:200],
            "placebo_effect_present": data.get("placebo_effect_present", False),
            "severity": data.get("severity", ""),
            "nocebo": data.get("nocebo", ""),
            "conditioning": data.get("conditioning", ""),
            "regression_to_mean": data.get("regression_to_mean", ""),
            "recommendation": data.get("recommendation", ""),
        }

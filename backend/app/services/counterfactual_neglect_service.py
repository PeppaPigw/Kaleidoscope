"""CounterfactualNeglectService — Counterfactual Neglect Detection.

Detects counterfactual neglect — failing to consider what would
have happened otherwise, leading to incorrect attribution of
effects to interventions or events.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COUNTERFACTUAL_NEGLECT_SYSTEM = """You are a counterfactual neglect specialist. Given a causal claim, assess whether counterfactual reasoning is missing:

Key concepts:
- Counterfactual: what would have happened without the intervention
- Base rate trajectory: where things were heading anyway
- Regression to mean: extreme values naturally reverting
- Selection effects: who/what was selected for intervention
- Natural recovery: improvement that would occur without action
- Placebo effect: improvement from belief in intervention
- Maturation: changes due to natural development over time

When counterfactual neglect IS present:
- Effect attributed without considering what would have happened anyway
- No control group or comparison scenario
- Base rate trajectory ignored
- Regression to mean not considered
- Natural recovery not accounted for
- Selection effects not addressed
- Before/after comparison without counterfactual

When counterfactual reasoning is present:
- Explicit consideration of alternative scenarios
- Control group or natural comparison used
- Base rate trajectory estimated
- Regression to mean accounted for
- Selection effects addressed
- Multiple counterfactual scenarios considered
- Causal attribution qualified by counterfactual uncertainty

Output JSON with: neglect_present (bool), severity (none/mild/moderate/severe), claim (what effect is attributed), intervention (what is credited), counterfactual (what would likely have happened anyway), confounds (what other explanations exist), recommendation (counterfactual_considered/mild_neglect/significant_attribution_error/major_counterfactual_gap/establish_counterfactual)."""

COUNTERFACTUAL_NEGLECT_PROMPT = """Detect counterfactual neglect:

Claim: {claim}
Intervention: {intervention}
Observed effect: {effect}
Baseline: {baseline}
Domain: {domain}
Context: {context}

Is counterfactual reasoning missing from this causal attribution? Return ONLY valid JSON."""


class CounterfactualNeglectService:
    """Detects counterfactual neglect — missing what-would-have-happened reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        intervention: str = "",
        effect: str = "",
        baseline: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect counterfactual neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COUNTERFACTUAL_NEGLECT_PROMPT.format(
                claim=claim,
                intervention=intervention or "Not specified",
                effect=effect or "Not specified",
                baseline=baseline or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COUNTERFACTUAL_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "neglect_present": data.get("neglect_present", False),
            "severity": data.get("severity", ""),
            "intervention": data.get("intervention", ""),
            "counterfactual": data.get("counterfactual", ""),
            "confounds": data.get("confounds", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicCounterfactualOutcomeBiasService — Epistemic Counterfactual Outcome Bias Detection.

Detects epistemic counterfactual outcome bias — counterfactual reasoning contaminated
by knowledge of actual outcomes, making alternatives seem more or less likely.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_OUTCOME_BIAS_SYSTEM = """You are an epistemic counterfactual outcome bias specialist. Given outcome-contaminated counterfactuals, assess distortion:

Key concepts:
- Epistemic counterfactual outcome bias: outcomes contaminating alternative reasoning
- Hindsight in counterfactuals: knowing outcome makes alternatives seem obvious
- Outcome-dependent plausibility: judging alternative plausibility by actual outcome
- Success bias: generating counterfactuals only for failures not successes
- Inevitability creep: actual outcome seeming increasingly inevitable
- Alternative dismissal: dismissing alternatives because they didn't happen
- Outcome anchoring: alternatives evaluated relative to known outcome

When epistemic counterfactual outcome bias IS present:
- Outcomes contaminating reasoning
- Hindsight making alternatives obvious
- Plausibility judged by outcome
- Only failure counterfactuals generated
- Actual outcome seeming inevitable
- Alternatives dismissed
- Outcome anchoring evaluation

When no counterfactual outcome bias:
- Outcomes bracketed
- Alternatives evaluated independently
- Plausibility judged ex ante
- Success and failure counterfactuals
- Contingency preserved
- Alternatives taken seriously
- Independent evaluation

Output JSON with: counterfactual_outcome_bias_detected (bool), severity (none/mild/moderate/severe), hindsight_in_counterfactuals (what hindsight contaminating), outcome_dependent_plausibility (what plausibility distorted), inevitability_creep (what seeming inevitable), alternative_dismissal (what alternatives dismissed), recommendation (no_counterfactual_outcome_bias/mild_outcome_bracketing/significant_ex_ante_reconstruction/major_intensive_blind_analysis/emergency_complete_counterfactual_outcome_bias)."""

EPISTEMIC_COUNTERFACTUAL_OUTCOME_BIAS_PROMPT = """Detect epistemic counterfactual outcome bias:

Hindsight in counterfactuals: {hindsight_in_counterfactuals}
Outcome-dependent plausibility: {outcome_dependent_plausibility}
Inevitability creep: {inevitability_creep}
Alternative dismissal: {alternative_dismissal}
Domain: {domain}
Context: {context}

Is counterfactual reasoning contaminated by known outcomes? Return ONLY valid JSON."""


class EpistemicCounterfactualOutcomeBiasService:
    """Detects epistemic counterfactual outcome bias — outcome contamination."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hindsight_in_counterfactuals: str,
        *,
        outcome_dependent_plausibility: str = "",
        inevitability_creep: str = "",
        alternative_dismissal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual outcome bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_OUTCOME_BIAS_PROMPT.format(
                hindsight_in_counterfactuals=hindsight_in_counterfactuals,
                outcome_dependent_plausibility=outcome_dependent_plausibility or "Not specified",
                inevitability_creep=inevitability_creep or "Not specified",
                alternative_dismissal=alternative_dismissal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_OUTCOME_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hindsight_in_counterfactuals": hindsight_in_counterfactuals[:200],
            "counterfactual_outcome_bias_detected": data.get("counterfactual_outcome_bias_detected", False),
            "severity": data.get("severity", ""),
            "outcome_dependent_plausibility": data.get("outcome_dependent_plausibility", ""),
            "inevitability_creep": data.get("inevitability_creep", ""),
            "alternative_dismissal": data.get("alternative_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }

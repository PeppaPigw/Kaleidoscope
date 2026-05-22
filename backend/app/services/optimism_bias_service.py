"""OptimismBiasService — Optimism Bias Detection.

Detects optimism bias — the systematic tendency to overestimate
the likelihood of positive events and underestimate negative ones.
Weinstein (1980). "It won't happen to me." Distinct from planning
fallacy (which is about time/cost) — optimism bias is about
outcomes and probabilities more broadly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OPTIMISM_SYSTEM = """You are an optimism bias specialist. Given a prediction or risk assessment, evaluate whether optimism bias is inflating expectations:

Key concepts (Weinstein, 1980; Sharot, 2011):
- Optimism bias: overestimating positive outcomes, underestimating negative ones
- Unrealistic optimism: "bad things happen to other people, not me"
- Comparative optimism: believing you're less at risk than peers
- Desirability bias: wanting something to be true makes you think it's more likely
- Asymmetric updating: incorporating good news but discounting bad news
- Illusion of control: believing you can influence random outcomes

When optimism bias IS present:
- Probability estimates are systematically too favorable
- Risks are acknowledged in general but dismissed for this specific case
- "It won't happen to me/us" reasoning
- Good news is weighted more heavily than bad news
- Desired outcomes are treated as likely outcomes
- Comparable failures are dismissed as irrelevant

When optimistic assessment MAY be warranted:
- Based on genuine competitive advantages
- Supported by track record of success
- Risks have been explicitly quantified and mitigated
- Upside scenarios are backed by specific mechanisms
- Assessment has been stress-tested against pessimistic scenarios

Output JSON with: optimism_bias_present (bool), severity (none/mild/moderate/severe), prediction (what positive outcome is expected), probability_claimed (what likelihood is being assigned), probability_realistic (what the base rate actually suggests), asymmetric_updating (bool — good news weighted more than bad?), comparative_optimism (bool — "we're different/better"?), desirability_bias (bool — wanting it makes it seem likely?), illusion_of_control (bool — overestimating ability to influence outcomes?), risks_acknowledged (what risks are recognized), risks_dismissed (what risks are being minimized), base_rate_evidence (what comparable situations actually show), specific_advantages (what genuine advantages exist), stress_test_done (bool — has the pessimistic case been examined?), downside_planning (what happens if the optimistic scenario doesn't materialize), recommendation (assessment_realistic/mild_optimism/significant_optimism_bias/major_probability_distortion/apply_base_rates)."""

OPTIMISM_PROMPT = """Detect optimism bias:

Prediction/Assessment: {prediction}
Evidence cited: {evidence}
Risks acknowledged: {risks}
Comparable outcomes: {comparables}
Domain: {domain}
Context: {context}

Is optimism bias inflating this assessment? Return ONLY valid JSON."""


class OptimismBiasService:
    """Detects optimism bias — systematic overestimation of positive outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        evidence: str = "",
        risks: str = "",
        comparables: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect optimism bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPTIMISM_PROMPT.format(
                prediction=prediction,
                evidence=evidence or "Not specified",
                risks=risks or "Not specified",
                comparables=comparables or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OPTIMISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "optimism_bias_present": data.get("optimism_bias_present", False),
            "severity": data.get("severity", ""),
            "prediction_detail": data.get("prediction", ""),
            "probability_claimed": data.get("probability_claimed", ""),
            "probability_realistic": data.get("probability_realistic", ""),
            "asymmetric_updating": data.get("asymmetric_updating", False),
            "comparative_optimism": data.get("comparative_optimism", False),
            "desirability_bias": data.get("desirability_bias", False),
            "illusion_of_control": data.get("illusion_of_control", False),
            "risks_acknowledged": data.get("risks_acknowledged", ""),
            "risks_dismissed": data.get("risks_dismissed", ""),
            "base_rate_evidence": data.get("base_rate_evidence", ""),
            "specific_advantages": data.get("specific_advantages", ""),
            "stress_test_done": data.get("stress_test_done", False),
            "downside_planning": data.get("downside_planning", ""),
            "recommendation": data.get("recommendation", ""),
        }

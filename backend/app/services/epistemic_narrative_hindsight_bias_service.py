"""EpistemicNarrativeHindsightBiasService - Hindsight Bias Detection.

Detects hindsight bias where past events seem predictable after the fact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_HINDSIGHT_BIAS_SYSTEM = """You are an epistemic narrative hindsight bias specialist. Given retrospective claims, assess whether hindsight bias distorts judgment:

Key concepts:
- Hindsight bias: believing past events were predictable after knowing the outcome
- Knew-it-all-along effect: claiming prior knowledge that didn't exist
- Outcome knowledge contamination: outcome information distorting memory of prior beliefs
- Foreseeability inflation: overestimating how predictable events were

When hindsight bias IS present:
- Past events claimed predictable
- Prior uncertainty forgotten
- Outcome knowledge contaminates judgment
- Foreseeability inflated
- Decision-makers unfairly judged

When no hindsight bias:
- Prior uncertainty acknowledged
- Prediction difficulty recognized
- Outcome knowledge separated from prior state
- Foreseeability realistically assessed
- Decision context preserved

Output JSON with: hindsight_bias_detected (bool), severity (none/mild/moderate/severe), knew_it_all_along (what claimed foreknowledge), outcome_contamination (what outcome contamination), foreseeability_inflation (what foreseeability inflated), recommendation (no_hindsight_bias/mild_uncertainty_restoration/significant_prior_state_analysis/major_decision_context_reconstruction/emergency_complete_hindsight_bias)."""

EPISTEMIC_NARRATIVE_HINDSIGHT_BIAS_PROMPT = """Detect epistemic narrative hindsight bias:

Retrospective claim: {retrospective_claim}
Knew it all along: {knew_it_all_along}
Outcome contamination: {outcome_contamination}
Foreseeability inflation: {foreseeability_inflation}
Domain: {domain}
Context: {context}

Is hindsight bias distorting judgment about past events? Return ONLY valid JSON."""


class EpistemicNarrativeHindsightBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        retrospective_claim: str,
        *,
        knew_it_all_along: str = "",
        outcome_contamination: str = "",
        foreseeability_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_HINDSIGHT_BIAS_PROMPT.format(
                retrospective_claim=retrospective_claim,
                knew_it_all_along=knew_it_all_along or "Not specified",
                outcome_contamination=outcome_contamination or "Not specified",
                foreseeability_inflation=foreseeability_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_HINDSIGHT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "retrospective_claim": retrospective_claim[:200],
            "hindsight_bias_detected": data.get("hindsight_bias_detected", False),
            "severity": data.get("severity", ""),
            "knew_it_all_along": data.get("knew_it_all_along", ""),
            "outcome_contamination": data.get("outcome_contamination", ""),
            "foreseeability_inflation": data.get("foreseeability_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }

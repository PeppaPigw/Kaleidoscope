"""IatrogenicsService — Iatrogenics Detection.

Identifies when an intervention causes more harm than the problem
it's trying to solve. Named after medical iatrogenesis (doctor-caused
illness), but applies broadly: regulations creating worse problems,
software fixes introducing more bugs, economic interventions
destabilizing markets. The cure is worse than the disease.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IATROGENICS_SYSTEM = """You are an iatrogenics specialist. Given an intervention, assess whether it causes more harm than the problem it addresses:
- Does the intervention create new problems worse than the original?
- Are the side effects of the intervention being properly weighed?
- Would doing nothing produce better outcomes than intervening?
- Is the intervention addressing symptoms while worsening root causes?
- Is there a naive interventionism bias (action bias) driving the intervention?

Output JSON with: iatrogenic_risk (bool), severity (none/mild/moderate/severe/catastrophic), intervention (what is being done), original_problem (what it's trying to fix), original_problem_severity (how bad the problem actually is: trivial/mild/moderate/severe/critical), intervention_harms (list of harms caused by the intervention), net_effect (positive/neutral/negative — overall impact vs doing nothing), harm_to_benefit_ratio (0-10 — higher means more harm relative to benefit), fragility_increased (bool — does the intervention make the system more fragile?), optionality_reduced (bool — does it close off future options?), who_benefits_from_intervention (who gains from intervening regardless of outcome), action_bias_present (bool — is there pressure to "do something" even if harmful?), do_nothing_outcome (what happens without intervention), minimal_intervention (smallest possible intervention that might work), reversibility_of_intervention (easy/moderate/hard/impossible to undo), time_horizon_mismatch (bool — short-term fix creating long-term harm?), recommendation (intervene/minimal_intervention/watchful_waiting/do_nothing/reverse_intervention)."""

IATROGENICS_PROMPT = """Detect iatrogenics:

Intervention: {intervention}
Problem being addressed: {problem}
Expected benefits: {expected_benefits}
System affected: {system}
Domain: {domain}
Context: {context}

Is this intervention iatrogenic? Return ONLY valid JSON."""


class IatrogenicsService:
    """Detects iatrogenic interventions — cures worse than the disease."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intervention: str,
        *,
        problem: str = "",
        expected_benefits: str = "",
        system: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect iatrogenics."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IATROGENICS_PROMPT.format(
                intervention=intervention,
                problem=problem or "Not specified",
                expected_benefits=expected_benefits or "Not specified",
                system=system or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IATROGENICS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intervention": intervention[:200],
            "iatrogenic_risk": data.get("iatrogenic_risk", False),
            "severity": data.get("severity", ""),
            "original_problem": data.get("original_problem", ""),
            "original_problem_severity": data.get("original_problem_severity", ""),
            "intervention_harms": data.get("intervention_harms", []),
            "net_effect": data.get("net_effect", ""),
            "harm_to_benefit_ratio": data.get("harm_to_benefit_ratio", 0),
            "fragility_increased": data.get("fragility_increased", False),
            "optionality_reduced": data.get("optionality_reduced", False),
            "who_benefits_from_intervention": data.get("who_benefits_from_intervention", ""),
            "action_bias_present": data.get("action_bias_present", False),
            "do_nothing_outcome": data.get("do_nothing_outcome", ""),
            "minimal_intervention": data.get("minimal_intervention", ""),
            "reversibility_of_intervention": data.get("reversibility_of_intervention", ""),
            "time_horizon_mismatch": data.get("time_horizon_mismatch", False),
            "recommendation": data.get("recommendation", ""),
        }

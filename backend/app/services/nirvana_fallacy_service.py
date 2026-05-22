"""NirvanaFallacyService — Nirvana Fallacy Detection.

Detects the nirvana fallacy (perfect solution fallacy) — rejecting
practical, imperfect solutions by comparing them to an unrealistic
ideal rather than to the status quo or other available options.
"Don't let the perfect be the enemy of the good." Related to
the politician's syllogism: "Something must be done. This is
something. Therefore, this must be done" (inverse).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NIRVANA_SYSTEM = """You are a nirvana fallacy specialist. Given a proposal and its criticism, assess whether the nirvana fallacy is at play:

Key concepts:
- Comparing a real solution to an idealized alternative that doesn't exist
- Rejecting "good" because it isn't "perfect"
- The relevant comparison is: proposed solution vs status quo (not vs ideal)
- Related: Voltaire's "the best is the enemy of the good"
- Opposite error: accepting any solution because "something must be done"

Assess:
- Is the criticism comparing the proposal to an achievable alternative or an ideal?
- What is the realistic comparison set (status quo, other feasible options)?
- Would the critic accept ANY solution, or is the bar set at perfection?
- Is the proposal being held to a higher standard than the status quo?
- Are legitimate criticisms being conflated with perfectionism?

Output JSON with: nirvana_fallacy_present (bool), severity (none/mild/moderate/severe), proposal (what is being proposed), criticism (what objection is being raised), comparison_target (what the proposal is being compared to: ideal/status_quo/feasible_alternative), ideal_invoked (what perfect solution is being implicitly demanded), realistic_alternatives (what actually achievable options exist), proposal_vs_status_quo (is the proposal better than doing nothing?), proposal_vs_alternatives (how it compares to other feasible options), legitimate_criticism_component (what part of the criticism is valid), perfectionism_component (what part demands the impossible), double_standard (bool — is the proposal held to higher standard than status quo?), who_benefits_from_inaction (who gains from rejecting the proposal), incremental_value (what the imperfect solution would still achieve), recommendation (criticism_valid/mostly_valid_some_perfectionism/significant_nirvana_fallacy/pure_perfectionism/accept_imperfect_solution)."""

NIRVANA_PROMPT = """Detect nirvana fallacy:

Proposal: {proposal}
Criticism: {criticism}
Alternatives: {alternatives}
Current situation: {current_situation}
Domain: {domain}
Context: {context}

Is the nirvana fallacy at play? Return ONLY valid JSON."""


class NirvanaFallacyService:
    """Detects nirvana fallacy — rejecting good because it isn't perfect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proposal: str,
        *,
        criticism: str = "",
        alternatives: str = "",
        current_situation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect nirvana fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NIRVANA_PROMPT.format(
                proposal=proposal,
                criticism=criticism or "Not specified",
                alternatives=alternatives or "Not specified",
                current_situation=current_situation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NIRVANA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proposal": proposal[:200],
            "nirvana_fallacy_present": data.get("nirvana_fallacy_present", False),
            "severity": data.get("severity", ""),
            "criticism": data.get("criticism", ""),
            "comparison_target": data.get("comparison_target", ""),
            "ideal_invoked": data.get("ideal_invoked", ""),
            "realistic_alternatives": data.get("realistic_alternatives", ""),
            "proposal_vs_status_quo": data.get("proposal_vs_status_quo", ""),
            "proposal_vs_alternatives": data.get("proposal_vs_alternatives", ""),
            "legitimate_criticism_component": data.get("legitimate_criticism_component", ""),
            "perfectionism_component": data.get("perfectionism_component", ""),
            "double_standard": data.get("double_standard", False),
            "who_benefits_from_inaction": data.get("who_benefits_from_inaction", ""),
            "incremental_value": data.get("incremental_value", ""),
            "recommendation": data.get("recommendation", ""),
        }

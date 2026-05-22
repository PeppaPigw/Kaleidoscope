"""EffortJustificationService — Effort Justification Detection.

Detects effort justification — valuing outcomes more because
of the effort invested rather than the objective quality.
Aronson & Mills (1959). Hazing makes groups seem more
valuable. Difficult processes make results seem better.
"It was hard, so it must be good."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EFFORT_JUSTIFICATION_SYSTEM = """You are an effort justification specialist. Given a valuation, assess whether the value assigned is inflated by the effort invested rather than reflecting objective quality:

Key concepts (Aronson & Mills, 1959; Festinger, 1957):
- Effort justification: valuing outcomes more because of effort invested
- Cognitive dissonance reduction: "I worked hard, so it must be worthwhile"
- Initiation effects: difficult entry makes groups seem more valuable
- Sunk cost interaction: effort already spent inflates perceived value
- IKEA effect overlap: but effort justification is broader than just creation
- Suffering-value link: "no pain, no gain" applied to quality judgments
- Process-outcome confusion: difficult process assumed to produce better results

When effort justification IS present:
- "It took so long, it must be good" without quality evidence
- Valuing a degree more because the program was grueling
- Rating a solution higher because it was hard to find
- Defending a decision because of the effort to reach it
- "We can't abandon this — we've put so much work in"
- Hazing/initiation making membership seem more valuable

When the valuation IS accurate:
- The effort genuinely produced higher quality (practice → skill)
- Objective measures confirm the value independent of effort
- The difficulty filtered for quality (hard exam → competent graduates)
- Others who didn't invest effort reach the same valuation
- The effort-value link is causal, not just correlational

Output JSON with: effort_justification_present (bool), severity (none/mild/moderate/severe), outcome (what is being valued), effort_invested (what effort was put in), objective_quality (what is the objective quality?), effort_inflated_value (how much is value inflated by effort?), quality_independent_of_effort (would the outcome be valued the same without the effort?), dissonance_reduction (bool — is this reducing cognitive dissonance?), sunk_cost_interaction (bool — is sunk cost thinking involved?), recommendation (valuation_accurate/mild_effort_inflation/significant_justification/major_effort_distortion/evaluate_quality_independently)."""

EFFORT_JUSTIFICATION_PROMPT = """Detect effort justification:

Valuation: {valuation}
Effort: {effort}
Quality evidence: {quality}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is the value inflated by effort invested rather than objective quality? Return ONLY valid JSON."""


class EffortJustificationService:
    """Detects effort justification — valuing outcomes more because of effort invested."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        valuation: str,
        *,
        effort: str = "",
        quality: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect effort justification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EFFORT_JUSTIFICATION_PROMPT.format(
                valuation=valuation,
                effort=effort or "Not specified",
                quality=quality or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EFFORT_JUSTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "valuation": valuation[:200],
            "effort_justification_present": data.get("effort_justification_present", False),
            "severity": data.get("severity", ""),
            "effort_invested": data.get("effort_invested", ""),
            "objective_quality": data.get("objective_quality", ""),
            "effort_inflated_value": data.get("effort_inflated_value", ""),
            "quality_independent_of_effort": data.get("quality_independent_of_effort", ""),
            "dissonance_reduction": data.get("dissonance_reduction", False),
            "sunk_cost_interaction": data.get("sunk_cost_interaction", False),
            "recommendation": data.get("recommendation", ""),
        }

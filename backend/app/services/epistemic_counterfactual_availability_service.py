"""EpistemicCounterfactualAvailabilityService — Epistemic Counterfactual Availability Detection.

Detects epistemic counterfactual availability — generating only easily-imagined
counterfactuals while missing less obvious but more relevant alternatives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_AVAILABILITY_SYSTEM = """You are an epistemic counterfactual availability specialist. Given counterfactual reasoning, assess availability distortion:

Key concepts:
- Epistemic counterfactual availability: only imagining easy alternatives
- Imagination constraint: limited by what's easy to visualize
- Salient alternative: focusing on dramatic rather than likely alternatives
- Narrative counterfactual: generating story-like rather than realistic alternatives
- Anchored counterfactual: alternatives too close to actual outcome
- Structural blindness: missing systemic alternatives for individual ones
- Creativity constraint: counterfactuals limited by cognitive fluency

When epistemic counterfactual availability IS present:
- Only easy alternatives imagined
- Imagination constraining analysis
- Dramatic alternatives favored
- Story-like alternatives generated
- Alternatives anchored to actual
- Systemic alternatives missed
- Cognitive fluency limiting options

When no counterfactual availability bias:
- Diverse alternatives considered
- Imagination not constraining
- Likely alternatives prioritized
- Realistic alternatives generated
- Full range explored
- Systemic alternatives included
- Creative alternatives generated

Output JSON with: counterfactual_availability_detected (bool), severity (none/mild/moderate/severe), imagination_constraint (what imagination constraining), salient_alternative (what dramatic alternatives favored), structural_blindness (what systemic alternatives missed), creativity_constraint (what fluency limiting), recommendation (no_counterfactual_availability/mild_alternative_expansion/significant_systematic_generation/major_intensive_counterfactual_analysis/emergency_complete_counterfactual_availability)."""

EPISTEMIC_COUNTERFACTUAL_AVAILABILITY_PROMPT = """Detect epistemic counterfactual availability:

Imagination constraint: {imagination_constraint}
Salient alternative: {salient_alternative}
Structural blindness: {structural_blindness}
Creativity constraint: {creativity_constraint}
Domain: {domain}
Context: {context}

Are only easily-imagined counterfactuals being generated? Return ONLY valid JSON."""


class EpistemicCounterfactualAvailabilityService:
    """Detects epistemic counterfactual availability — imagination-limited alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        imagination_constraint: str,
        *,
        salient_alternative: str = "",
        structural_blindness: str = "",
        creativity_constraint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual availability."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_AVAILABILITY_PROMPT.format(
                imagination_constraint=imagination_constraint,
                salient_alternative=salient_alternative or "Not specified",
                structural_blindness=structural_blindness or "Not specified",
                creativity_constraint=creativity_constraint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_AVAILABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "imagination_constraint": imagination_constraint[:200],
            "counterfactual_availability_detected": data.get("counterfactual_availability_detected", False),
            "severity": data.get("severity", ""),
            "salient_alternative": data.get("salient_alternative", ""),
            "structural_blindness": data.get("structural_blindness", ""),
            "creativity_constraint": data.get("creativity_constraint", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicCounterfactualProximityService — Epistemic Counterfactual Proximity Detection.

Detects epistemic counterfactual proximity — near-miss events distorting probability
assessment by making outcomes seem more mutable than they actually were.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_PROXIMITY_SYSTEM = """You are an epistemic counterfactual proximity specialist. Given proximity effects, assess probability distortion:

Key concepts:
- Epistemic counterfactual proximity: near-misses distorting probability
- Close call effect: almost-events seeming more likely to recur
- Temporal proximity: events close in time seeming more mutable
- Spatial proximity: events close in space seeming more preventable
- Emotional amplification: near-misses generating disproportionate emotion
- Probability inflation: near-misses inflating perceived probability
- Mutability illusion: close outcomes seeming more changeable

When epistemic counterfactual proximity IS present:
- Near-misses distorting probability
- Close calls inflating recurrence
- Temporal proximity creating mutability
- Spatial proximity creating preventability
- Emotions amplified by proximity
- Probabilities inflated
- Outcomes seeming more mutable

When no proximity bias:
- Near-misses properly weighted
- Close calls not inflating probability
- Temporal distance not affecting mutability
- Spatial distance not affecting assessment
- Emotions proportionate
- Probabilities accurate
- Mutability properly assessed

Output JSON with: counterfactual_proximity_detected (bool), severity (none/mild/moderate/severe), close_call_effect (what close calls inflating), temporal_proximity (what temporal proximity distorting), probability_inflation (what probabilities inflated), mutability_illusion (what seeming more mutable), recommendation (no_counterfactual_proximity/mild_probability_correction/significant_base_rate_anchoring/major_intensive_statistical_analysis/emergency_complete_counterfactual_proximity)."""

EPISTEMIC_COUNTERFACTUAL_PROXIMITY_PROMPT = """Detect epistemic counterfactual proximity:

Close call effect: {close_call_effect}
Temporal proximity: {temporal_proximity}
Probability inflation: {probability_inflation}
Mutability illusion: {mutability_illusion}
Domain: {domain}
Context: {context}

Are near-miss events distorting probability assessment? Return ONLY valid JSON."""


class EpistemicCounterfactualProximityService:
    """Detects epistemic counterfactual proximity — near-miss probability distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        close_call_effect: str,
        *,
        temporal_proximity: str = "",
        probability_inflation: str = "",
        mutability_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual proximity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_PROXIMITY_PROMPT.format(
                close_call_effect=close_call_effect,
                temporal_proximity=temporal_proximity or "Not specified",
                probability_inflation=probability_inflation or "Not specified",
                mutability_illusion=mutability_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_PROXIMITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "close_call_effect": close_call_effect[:200],
            "counterfactual_proximity_detected": data.get("counterfactual_proximity_detected", False),
            "severity": data.get("severity", ""),
            "temporal_proximity": data.get("temporal_proximity", ""),
            "probability_inflation": data.get("probability_inflation", ""),
            "mutability_illusion": data.get("mutability_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

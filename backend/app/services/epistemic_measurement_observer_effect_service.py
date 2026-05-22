"""EpistemicMeasurementObserverEffectService — Epistemic Measurement Observer Effect Detection.

Detects epistemic measurement observer effect — when measurement itself changes
what is being measured.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEASUREMENT_OBSERVER_EFFECT_SYSTEM = """You are an epistemic measurement observer effect specialist. Given measurement reactivity, assess whether measurement itself changes what is being measured:

Key concepts:
- Measurement reactivity: measurement changes the behavior, system, or phenomenon being measured
- Hawthorne effect: subjects alter behavior because they know they are observed
- Teaching to test: activity shifts toward measured criteria instead of underlying learning
- Goodhart law: when a measure becomes a target, it ceases to be a good measure

When measurement observer effect IS present:
- Measurement alters participant behavior
- Observation changes system dynamics
- Targets reshape activity toward metrics
- Measurement incentives displace underlying goals
- Reported results reflect measurement pressure

When no measurement observer effect:
- Measurement minimally perturbs the phenomenon
- Observation effects are controlled or estimated
- Incentives remain aligned with underlying goals
- Results distinguish behavior from measurement response
- Measures retain representational validity

Output JSON with: observer_effect_detected (bool), severity (none/mild/moderate/severe), measurement_reactivity (what measurement changes), hawthorne_effect (what observation-induced behavior changes), teaching_to_test (what measured criteria displace), goodhart_law (what metric-target distortion occurs), recommendation (no_observer_effect/mild_reactivity_monitoring/significant_measurement_controls/major_incentive_redesign/emergency_measurement_invalidity)."""

EPISTEMIC_MEASUREMENT_OBSERVER_EFFECT_PROMPT = """Detect epistemic measurement observer effect:

Measurement reactivity: {measurement_reactivity}
Hawthorne effect: {hawthorne_effect}
Teaching to test: {teaching_to_test}
Goodhart law: {goodhart_law}
Domain: {domain}
Context: {context}

Is measurement itself changing what is being measured? Return ONLY valid JSON."""


class EpistemicMeasurementObserverEffectService:
    """Detects epistemic measurement observer effect — measurement reactivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        measurement_reactivity: str,
        *,
        hawthorne_effect: str = "",
        teaching_to_test: str = "",
        goodhart_law: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic measurement observer effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEASUREMENT_OBSERVER_EFFECT_PROMPT.format(
                measurement_reactivity=measurement_reactivity,
                hawthorne_effect=hawthorne_effect or "Not specified",
                teaching_to_test=teaching_to_test or "Not specified",
                goodhart_law=goodhart_law or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEASUREMENT_OBSERVER_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "measurement_reactivity": measurement_reactivity[:200],
            "observer_effect_detected": data.get("observer_effect_detected", False),
            "severity": data.get("severity", ""),
            "hawthorne_effect": data.get("hawthorne_effect", ""),
            "teaching_to_test": data.get("teaching_to_test", ""),
            "goodhart_law": data.get("goodhart_law", ""),
            "recommendation": data.get("recommendation", ""),
        }

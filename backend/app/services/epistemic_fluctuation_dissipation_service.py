"""EpistemicFluctuationDissipationService — Epistemic Fluctuation-Dissipation Detection.

Detects epistemic fluctuation-dissipation — relationship between random
intellectual fluctuations and the system's response to external perturbation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FLUCTUATION_DISSIPATION_SYSTEM = """You are an epistemic fluctuation-dissipation specialist. Given an intellectual system, assess whether random fluctuations relate to perturbation response:

Key concepts:
- Epistemic fluctuation-dissipation: fluctuations predicting response
- Thermal noise: random fluctuations from intellectual temperature
- Response function: how system responds to external push
- Einstein relation: connecting diffusion to mobility
- Kubo formula: relating correlation to response
- Equilibrium: state where theorem holds exactly
- Violation: non-equilibrium breaking the relation

When epistemic fluctuation-dissipation IS present:
- Random fluctuations predicting response to perturbation
- Thermal noise proportional to intellectual temperature
- Measurable response to external intellectual push
- Connection between random motion and directed response
- Correlation functions predicting response functions
- System in or near intellectual equilibrium
- Violations indicating non-equilibrium

When independent fluctuation-response is present:
- Fluctuations not predicting response
- Noise unrelated to temperature
- Response unrelated to fluctuations
- No connection between random and directed
- Correlation not predicting response
- System far from equilibrium
- No theorem to violate

Output JSON with: fluctuation_dissipation_present (bool), severity (none/mild/moderate/severe), thermal_noise (what random fluctuations), response_function (what perturbation response), einstein_relation (what diffusion-mobility connection), violation (what non-equilibrium breaking), recommendation (independent_fluctuation/mild_relation/significant_fluctuation_dissipation/major_equilibrium_constraint/check_for_violations)."""

EPISTEMIC_FLUCTUATION_DISSIPATION_PROMPT = """Detect epistemic fluctuation-dissipation:

Thermal noise: {thermal_noise}
Response function: {response_function}
Einstein relation: {einstein_relation}
Violation: {violation}
Domain: {domain}
Context: {context}

Is there a relationship between random intellectual fluctuations and the system's response to external perturbation? Return ONLY valid JSON."""


class EpistemicFluctuationDissipationService:
    """Detects epistemic fluctuation-dissipation — fluctuations predicting response."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thermal_noise: str,
        *,
        response_function: str = "",
        einstein_relation: str = "",
        violation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fluctuation-dissipation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FLUCTUATION_DISSIPATION_PROMPT.format(
                thermal_noise=thermal_noise,
                response_function=response_function or "Not specified",
                einstein_relation=einstein_relation or "Not specified",
                violation=violation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FLUCTUATION_DISSIPATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thermal_noise": thermal_noise[:200],
            "fluctuation_dissipation_present": data.get("fluctuation_dissipation_present", False),
            "severity": data.get("severity", ""),
            "response_function": data.get("response_function", ""),
            "einstein_relation": data.get("einstein_relation", ""),
            "violation": data.get("violation", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMorphogenGradientService — Epistemic Morphogen Gradient Detection.

Detects epistemic morphogen gradient — concentration gradient of ideas
determining intellectual fate based on position within the gradient.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MORPHOGEN_GRADIENT_SYSTEM = """You are an epistemic morphogen gradient specialist. Given an intellectual space, assess whether idea concentration determines fate:

Key concepts:
- Epistemic morphogen gradient: concentration determining intellectual fate
- Threshold: concentration level triggering different fates
- Source: origin point of the gradient
- Diffusion: how the signal spreads from source
- Positional information: fate determined by location
- French flag model: distinct zones from single gradient
- Robustness: gradient working despite noise

When epistemic morphogen gradient IS present:
- Concentration of ideas determining intellectual fate
- Different concentration levels triggering different outcomes
- Clear origin point of the intellectual signal
- Signal spreading from source through diffusion
- Intellectual fate determined by position in gradient
- Distinct zones created from single gradient
- Gradient functioning despite noise and perturbation

When uniform field is present:
- No concentration gradient
- No threshold effects
- No clear signal source
- No diffusion pattern
- Fate independent of position
- No distinct zones
- No robustness needed

Output JSON with: morphogen_gradient_present (bool), severity (none/mild/moderate/severe), threshold (what concentration triggers), source (what origin point), positional_information (what position determines), robustness (what noise tolerance), recommendation (uniform_field/mild_gradient/significant_morphogen_gradient/major_fate_determination/map_gradient_thresholds)."""

EPISTEMIC_MORPHOGEN_GRADIENT_PROMPT = """Detect epistemic morphogen gradient:

Threshold: {threshold}
Source: {source}
Positional information: {positional_information}
Robustness: {robustness}
Domain: {domain}
Context: {context}

Is a concentration gradient of ideas determining intellectual fate based on position? Return ONLY valid JSON."""


class EpistemicMorphogenGradientService:
    """Detects epistemic morphogen gradient — concentration determining fate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threshold: str,
        *,
        source: str = "",
        positional_information: str = "",
        robustness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic morphogen gradient."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MORPHOGEN_GRADIENT_PROMPT.format(
                threshold=threshold,
                source=source or "Not specified",
                positional_information=positional_information or "Not specified",
                robustness=robustness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MORPHOGEN_GRADIENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threshold": threshold[:200],
            "morphogen_gradient_present": data.get("morphogen_gradient_present", False),
            "severity": data.get("severity", ""),
            "source": data.get("source", ""),
            "positional_information": data.get("positional_information", ""),
            "robustness": data.get("robustness", ""),
            "recommendation": data.get("recommendation", ""),
        }

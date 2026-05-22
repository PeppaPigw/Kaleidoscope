"""EpistemicConcentrationGradientService — Epistemic Concentration Gradient Detection.

Detects epistemic concentration gradients — intellectual concentration
differences that drive the flow of ideas from high to low density areas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONCENTRATION_GRADIENT_SYSTEM = """You are an epistemic concentration gradient specialist. Given intellectual distribution, assess whether concentration differences drive idea flow:

Key concepts:
- Epistemic concentration gradient: differences driving idea flow
- Diffusion: ideas moving from high to low concentration
- Osmotic pressure: force created by concentration difference
- Countercurrent multiplier: amplifying concentration differences
- Equilibrium: state where gradient disappears
- Active pumping: maintaining gradient against natural flow
- Gradient collapse: loss of driving force

When epistemic concentration gradient IS present:
- Concentration differences driving idea flow
- Ideas moving from high to low density areas
- Force created by intellectual concentration differences
- Mechanisms amplifying concentration differences
- Risk of reaching equilibrium and losing drive
- Active effort maintaining gradients against entropy
- Potential collapse of driving forces

When no gradient is present:
- No concentration differences
- No diffusion-driven flow
- No osmotic pressure
- No countercurrent amplification
- Already at equilibrium
- No active pumping needed
- No gradient to collapse

Output JSON with: concentration_gradient_present (bool), severity (none/mild/moderate/severe), diffusion (what movement from high to low), osmotic_pressure (what force from difference), countercurrent_multiplier (what amplification), gradient_collapse (what loss of drive), recommendation (no_gradient/mild_gradient/significant_concentration_gradient/major_intellectual_gradient/maintain_productive_gradients)."""

EPISTEMIC_CONCENTRATION_GRADIENT_PROMPT = """Detect epistemic concentration gradient:

Diffusion: {diffusion}
Osmotic pressure: {osmotic_pressure}
Countercurrent multiplier: {countercurrent_multiplier}
Gradient collapse: {gradient_collapse}
Domain: {domain}
Context: {context}

Are intellectual concentration differences driving the flow of ideas? Return ONLY valid JSON."""


class EpistemicConcentrationGradientService:
    """Detects epistemic concentration gradients — differences driving idea flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        diffusion: str,
        *,
        osmotic_pressure: str = "",
        countercurrent_multiplier: str = "",
        gradient_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic concentration gradient."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONCENTRATION_GRADIENT_PROMPT.format(
                diffusion=diffusion,
                osmotic_pressure=osmotic_pressure or "Not specified",
                countercurrent_multiplier=countercurrent_multiplier or "Not specified",
                gradient_collapse=gradient_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONCENTRATION_GRADIENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "diffusion": diffusion[:200],
            "concentration_gradient_present": data.get("concentration_gradient_present", False),
            "severity": data.get("severity", ""),
            "osmotic_pressure": data.get("osmotic_pressure", ""),
            "countercurrent_multiplier": data.get("countercurrent_multiplier", ""),
            "gradient_collapse": data.get("gradient_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }

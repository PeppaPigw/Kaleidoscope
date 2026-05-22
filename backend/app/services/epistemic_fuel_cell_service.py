"""EpistemicFuelCellService — Epistemic Fuel Cell Detection.

Detects epistemic fuel cell — ideas continuously converting intellectual
fuel into useful energy without combustion or degradation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FUEL_CELL_SYSTEM = """You are an epistemic fuel cell specialist. Given an energy conversion pattern, assess whether ideas continuously convert fuel into energy without combustion:

Key concepts:
- Epistemic fuel cell: continuous conversion without combustion
- Fuel: intellectual input continuously consumed
- Oxidant: what reacts with the fuel
- Membrane: selective barrier between fuel and oxidant
- Efficiency: how much useful energy vs waste
- Poisoning: contaminants degrading the catalyst
- Stack: multiple cells combined for more power

When epistemic fuel cell IS present:
- Ideas continuously converting intellectual fuel into energy
- Intellectual input being continuously consumed
- Reactant combining with the fuel
- Selective barrier controlling the reaction
- Varying efficiency of the conversion
- Contaminants degrading the conversion process
- Multiple conversion units combined for more output

When combustion is present:
- Ideas burning fuel in uncontrolled reaction
- Fuel consumed in single burst
- Uncontrolled reaction with oxidant
- No selective barrier
- Low efficiency with much waste
- No catalyst to poison
- Single reaction not stackable

Output JSON with: fuel_cell_present (bool), severity (none/mild/moderate/severe), fuel (what intellectual input), membrane (what selective barrier), efficiency (what conversion rate), poisoning (what degrades process), recommendation (combustion_mode/mild_fuel_cell/significant_fuel_cell/major_continuous_conversion/diversify_fuel_sources)."""

EPISTEMIC_FUEL_CELL_PROMPT = """Detect epistemic fuel cell:

Fuel: {fuel}
Membrane: {membrane}
Efficiency: {efficiency}
Poisoning: {poisoning}
Domain: {domain}
Context: {context}

Are ideas continuously converting intellectual fuel into useful energy without combustion or degradation? Return ONLY valid JSON."""


class EpistemicFuelCellService:
    """Detects epistemic fuel cell — continuous conversion without combustion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fuel: str,
        *,
        membrane: str = "",
        efficiency: str = "",
        poisoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fuel cell."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FUEL_CELL_PROMPT.format(
                fuel=fuel,
                membrane=membrane or "Not specified",
                efficiency=efficiency or "Not specified",
                poisoning=poisoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FUEL_CELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fuel": fuel[:200],
            "fuel_cell_present": data.get("fuel_cell_present", False),
            "severity": data.get("severity", ""),
            "membrane": data.get("membrane", ""),
            "efficiency": data.get("efficiency", ""),
            "poisoning": data.get("poisoning", ""),
            "recommendation": data.get("recommendation", ""),
        }

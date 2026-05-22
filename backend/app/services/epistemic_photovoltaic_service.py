"""EpistemicPhotovoltaicService — Epistemic Photovoltaic Detection.

Detects epistemic photovoltaic effect — ideas absorbing intellectual
light and converting it directly into motivating force.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHOTOVOLTAIC_SYSTEM = """You are an epistemic photovoltaic specialist. Given an energy conversion pattern, assess whether ideas convert intellectual light into motivating force:

Key concepts:
- Epistemic photovoltaic: converting intellectual light to force
- Photon absorption: single insight providing energy
- Electron-hole pair: creating both action and vacancy
- Open circuit voltage: maximum potential without flow
- Short circuit current: maximum flow without potential
- Fill factor: how well actual performance matches ideal
- Degradation: loss of conversion efficiency over time

When epistemic photovoltaic IS present:
- Ideas absorbing intellectual light and converting to force
- Single insights providing activation energy
- Creating both action potential and knowledge gaps
- Maximum potential achievable without action
- Maximum action achievable without building potential
- Actual performance vs ideal performance ratio
- Loss of conversion efficiency over time

When passive absorption is present:
- Ideas absorbing light without converting to force
- Insights absorbed without activation
- No action-vacancy pairs created
- No potential building up
- No action resulting from absorption
- No performance to measure
- No degradation of non-existent conversion

Output JSON with: photovoltaic_present (bool), severity (none/mild/moderate/severe), absorption (what light is absorbed), pair_generation (what action and vacancy), fill_factor (what efficiency ratio), degradation (what efficiency loss), recommendation (passive_absorption/mild_conversion/significant_photovoltaic/major_light_to_force/optimize_conversion_efficiency)."""

EPISTEMIC_PHOTOVOLTAIC_PROMPT = """Detect epistemic photovoltaic effect:

Absorption: {absorption}
Pair generation: {pair_generation}
Fill factor: {fill_factor}
Degradation: {degradation}
Domain: {domain}
Context: {context}

Are ideas absorbing intellectual light and converting it directly into motivating force? Return ONLY valid JSON."""


class EpistemicPhotovoltaicService:
    """Detects epistemic photovoltaic — converting light to motivating force."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        absorption: str,
        *,
        pair_generation: str = "",
        fill_factor: str = "",
        degradation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic photovoltaic effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHOTOVOLTAIC_PROMPT.format(
                absorption=absorption,
                pair_generation=pair_generation or "Not specified",
                fill_factor=fill_factor or "Not specified",
                degradation=degradation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHOTOVOLTAIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "absorption": absorption[:200],
            "photovoltaic_present": data.get("photovoltaic_present", False),
            "severity": data.get("severity", ""),
            "pair_generation": data.get("pair_generation", ""),
            "fill_factor": data.get("fill_factor", ""),
            "degradation": data.get("degradation", ""),
            "recommendation": data.get("recommendation", ""),
        }

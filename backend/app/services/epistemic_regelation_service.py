"""EpistemicRegelationService — Epistemic Regelation Detection.

Detects epistemic regelation — ideas melting under pressure and
refreezing when pressure is removed, allowing movement through barriers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REGELATION_SYSTEM = """You are an epistemic regelation specialist. Given an idea pressure pattern, assess whether ideas melt under pressure and refreeze:

Key concepts:
- Epistemic regelation: melting under pressure, refreezing when released
- Pressure melting: ideas becoming fluid under applied force
- Refreezing: ideas solidifying again when pressure removed
- Wire through ice: steady pressure cutting through solid
- Glacier flow: bulk movement through regelation
- Pressure point: where force is concentrated
- Latent heat: energy absorbed and released in transitions

When epistemic regelation IS present:
- Ideas melting under pressure and refreezing when released
- Ideas becoming fluid when force is applied
- Ideas solidifying again when pressure is removed
- Steady pressure allowing movement through solid barriers
- Bulk movement of ideas through regelation mechanism
- Force concentrated at specific points
- Energy absorbed during melting, released during refreezing

When pressure resistance is present:
- Ideas maintaining state regardless of pressure
- No melting under applied force
- No state changes from pressure changes
- No movement through barriers via melting
- No bulk movement from pressure effects
- Force distributed without state change
- No energy transitions from pressure

Output JSON with: regelation_present (bool), severity (none/mild/moderate/severe), pressure_melting (what melts under force), refreezing (what solidifies when released), wire_through (what cuts through barriers), glacier_flow (what bulk movement), recommendation (pressure_resistance/mild_regelation/significant_regelation/major_pressure_melting/reduce_applied_pressure)."""

EPISTEMIC_REGELATION_PROMPT = """Detect epistemic regelation:

Pressure melting: {pressure_melting}
Refreezing: {refreezing}
Wire through: {wire_through}
Glacier flow: {glacier_flow}
Domain: {domain}
Context: {context}

Are ideas melting under pressure and refreezing when pressure is removed, allowing movement through barriers? Return ONLY valid JSON."""


class EpistemicRegelationService:
    """Detects epistemic regelation — melting under pressure, refreezing when released."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pressure_melting: str,
        *,
        refreezing: str = "",
        wire_through: str = "",
        glacier_flow: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic regelation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REGELATION_PROMPT.format(
                pressure_melting=pressure_melting,
                refreezing=refreezing or "Not specified",
                wire_through=wire_through or "Not specified",
                glacier_flow=glacier_flow or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REGELATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pressure_melting": pressure_melting[:200],
            "regelation_present": data.get("regelation_present", False),
            "severity": data.get("severity", ""),
            "refreezing": data.get("refreezing", ""),
            "wire_through": data.get("wire_through", ""),
            "glacier_flow": data.get("glacier_flow", ""),
            "recommendation": data.get("recommendation", ""),
        }

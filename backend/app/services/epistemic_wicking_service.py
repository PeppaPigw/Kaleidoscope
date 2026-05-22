"""EpistemicWickingService — Epistemic Wicking Detection.

Detects epistemic wicking — ideas being absorbed and transported
through porous intellectual materials by capillary forces.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WICKING_SYSTEM = """You are an epistemic wicking specialist. Given an idea absorption pattern, assess whether ideas are transported through porous materials:

Key concepts:
- Epistemic wicking: ideas absorbed and transported through porous material
- Porosity: how many channels exist in the material
- Absorption: ideas being drawn into the material
- Transport: movement through the porous structure
- Saturation: material fully loaded with ideas
- Evaporation: ideas leaving the material at the surface
- Wetting front: advancing edge of idea absorption

When epistemic wicking IS present:
- Ideas absorbed and transported through porous intellectual materials
- Many channels existing in the intellectual structure
- Ideas being drawn into the material spontaneously
- Movement through the porous structure without external force
- Material becoming fully saturated with ideas
- Ideas leaving the material at exposed surfaces
- Advancing front of idea absorption through material

When impermeable surface is present:
- Ideas not absorbed into material
- No channels in the structure
- Ideas remaining on the surface
- No internal transport
- No saturation possible
- No evaporation from within
- No advancing absorption front

Output JSON with: wicking_present (bool), severity (none/mild/moderate/severe), porosity (what channels exist), absorption (what is drawn in), saturation (what is fully loaded), evaporation (what leaves at surface), recommendation (impermeable_boundary/mild_absorption/significant_wicking/major_porous_transport/control_porosity)."""

EPISTEMIC_WICKING_PROMPT = """Detect epistemic wicking:

Porosity: {porosity}
Absorption: {absorption}
Saturation: {saturation}
Evaporation: {evaporation}
Domain: {domain}
Context: {context}

Are ideas being absorbed and transported through porous intellectual materials by capillary forces? Return ONLY valid JSON."""


class EpistemicWickingService:
    """Detects epistemic wicking — ideas transported through porous materials."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        porosity: str,
        *,
        absorption: str = "",
        saturation: str = "",
        evaporation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic wicking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WICKING_PROMPT.format(
                porosity=porosity,
                absorption=absorption or "Not specified",
                saturation=saturation or "Not specified",
                evaporation=evaporation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WICKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "porosity": porosity[:200],
            "wicking_present": data.get("wicking_present", False),
            "severity": data.get("severity", ""),
            "absorption": data.get("absorption", ""),
            "saturation": data.get("saturation", ""),
            "evaporation": data.get("evaporation", ""),
            "recommendation": data.get("recommendation", ""),
        }

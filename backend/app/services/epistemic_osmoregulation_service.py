"""EpistemicOsmoregulationService — Epistemic Osmoregulation Detection.

Detects epistemic osmoregulation — controlling the concentration of
intellectual content to prevent dilution or toxic concentration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OSMOREGULATION_SYSTEM = """You are an epistemic osmoregulation specialist. Given an intellectual concentration pattern, assess whether content concentration is being actively controlled:

Key concepts:
- Epistemic osmoregulation: controlling intellectual concentration
- Osmotic pressure: force from concentration differences
- Dilution: ideas becoming too watered down
- Concentration: ideas becoming too dense/toxic
- Semipermeable membrane: selective barrier to ideas
- Tonicity: relative concentration inside vs outside
- Dehydration: loss of intellectual substance

When epistemic osmoregulation IS present:
- Active control of intellectual content concentration
- Pressure from concentration differences across boundaries
- Ideas becoming too diluted to be effective
- Ideas becoming too concentrated/toxic
- Selective barriers controlling what enters/exits
- Imbalance between internal and external concentration
- Loss of intellectual substance through osmotic pressure

When free diffusion is present:
- No control of intellectual concentration
- No pressure from concentration differences
- Ideas at natural equilibrium concentration
- No toxic concentration buildup
- No selective barriers
- Balance between internal and external
- No substance loss

Output JSON with: osmoregulation_present (bool), severity (none/mild/moderate/severe), pressure (what osmotic pressure exists), dilution (what is being diluted), concentration (what is too concentrated), membrane (what selective barrier), recommendation (free_diffusion/mild_regulation/significant_osmoregulation/major_concentration_control/restore_natural_balance)."""

EPISTEMIC_OSMOREGULATION_PROMPT = """Detect epistemic osmoregulation:

Pressure: {pressure}
Dilution: {dilution}
Concentration: {concentration}
Membrane: {membrane}
Domain: {domain}
Context: {context}

Is the concentration of intellectual content being actively controlled to prevent dilution or toxic concentration? Return ONLY valid JSON."""


class EpistemicOsmoregulationService:
    """Detects epistemic osmoregulation — controlling intellectual concentration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pressure: str,
        *,
        dilution: str = "",
        concentration: str = "",
        membrane: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic osmoregulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OSMOREGULATION_PROMPT.format(
                pressure=pressure,
                dilution=dilution or "Not specified",
                concentration=concentration or "Not specified",
                membrane=membrane or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OSMOREGULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pressure": pressure[:200],
            "osmoregulation_present": data.get("osmoregulation_present", False),
            "severity": data.get("severity", ""),
            "dilution": data.get("dilution", ""),
            "concentration": data.get("concentration", ""),
            "membrane": data.get("membrane", ""),
            "recommendation": data.get("recommendation", ""),
        }

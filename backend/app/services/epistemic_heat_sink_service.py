"""EpistemicHeatSinkService — Epistemic Heat Sink Detection.

Detects epistemic heat sink — knowledge energy dissipating into
useless forms, productive intellectual energy wasted.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HEAT_SINK_SYSTEM = """You are an epistemic heat sink specialist. Given a knowledge energy pattern, assess whether productive energy is dissipating:

Key concepts:
- Epistemic heat sink: productive knowledge energy dissipating into waste
- Energy dissipation: useful intellectual energy becoming useless heat
- Productive waste: productive capacity wasted on unproductive activities
- Friction loss: energy lost to intellectual friction
- Thermal noise: random noise consuming energy
- Cooling: productive energy cooling into inaction
- Waste heat: byproduct energy that cannot be recovered

When heat sink IS present:
- Productive knowledge energy dissipating into waste
- Useful intellectual energy becoming useless
- Productive capacity wasted on unproductive activities
- Energy lost to intellectual friction and bureaucracy
- Random noise consuming productive energy
- Productive energy cooling into inaction
- Byproduct energy that cannot be recovered

When productive energy is present:
- Knowledge energy directed productively
- Intellectual energy producing useful results
- Productive capacity applied effectively
- Minimal energy lost to friction
- Signal dominating over noise
- Energy maintained at productive levels
- Energy efficiently converted to useful work

Output JSON with: heat_sink_present (bool), severity (none/mild/moderate/severe), energy (what energy dissipates), sink (where energy goes), waste (what waste results), recovery (whether energy can be recovered), recommendation (productive_energy/mild_dissipation/significant_heat_sink/major_energy_waste/redirect_energy)."""

EPISTEMIC_HEAT_SINK_PROMPT = """Detect epistemic heat sink:

Energy: {energy}
Sink: {sink}
Waste: {waste}
Recovery: {recovery}
Domain: {domain}
Context: {context}

Is productive knowledge energy dissipating into useless forms? Return ONLY valid JSON."""


class EpistemicHeatSinkService:
    """Detects epistemic heat sink — productive energy dissipating into waste."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        energy: str,
        *,
        sink: str = "",
        waste: str = "",
        recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic heat sink."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HEAT_SINK_PROMPT.format(
                energy=energy,
                sink=sink or "Not specified",
                waste=waste or "Not specified",
                recovery=recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HEAT_SINK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "energy": energy[:200],
            "heat_sink_present": data.get("heat_sink_present", False),
            "severity": data.get("severity", ""),
            "sink": data.get("sink", ""),
            "waste": data.get("waste", ""),
            "recovery": data.get("recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }

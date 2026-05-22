"""EpistemicHeatDeathService — Epistemic Heat Death Detection.

Detects epistemic heat death — all intellectual energy dissipated,
no useful cognitive work possible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HEAT_DEATH_SYSTEM = """You are an epistemic heat death specialist. Given an intellectual environment, assess whether all useful intellectual energy has been dissipated:

Key concepts:
- Epistemic heat death: all intellectual energy dissipated
- Cognitive exhaustion: no energy left for useful thinking
- Debate fatigue: all positions exhausted without resolution
- Innovation death: no new ideas possible in the space
- Intellectual stagnation: complete stagnation of thought
- Equilibrium trap: system at equilibrium with no driving force
- Creative death: creativity completely exhausted

When epistemic heat death IS present:
- All intellectual energy dissipated
- No energy left for useful cognitive work
- All positions exhausted without resolution
- No new ideas possible in the space
- Complete stagnation of thought
- System at equilibrium with no driving force
- Creativity completely exhausted

When productive rest is present:
- Temporary pause before renewed activity
- Energy being conserved for future use
- Consolidation phase before new exploration
- Rest enabling future productivity
- Pause reflecting rather than exhaustion
- Equilibrium as temporary state
- Creativity recharging

Output JSON with: heat_death_present (bool), severity (none/mild/moderate/severe), environment (what environment is affected), exhaustion (what is exhausted), stagnation (how stagnation manifests), energy (what happened to intellectual energy), recommendation (productive_rest/mild_fatigue/significant_heat_death/major_intellectual_death/inject_new_energy)."""

EPISTEMIC_HEAT_DEATH_PROMPT = """Detect epistemic heat death:

Environment: {environment}
Exhaustion: {exhaustion}
Stagnation: {stagnation}
Energy: {energy}
Domain: {domain}
Context: {context}

Has all intellectual energy been dissipated with no useful work possible? Return ONLY valid JSON."""


class EpistemicHeatDeathService:
    """Detects epistemic heat death — all intellectual energy dissipated."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        exhaustion: str = "",
        stagnation: str = "",
        energy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic heat death."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HEAT_DEATH_PROMPT.format(
                environment=environment,
                exhaustion=exhaustion or "Not specified",
                stagnation=stagnation or "Not specified",
                energy=energy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HEAT_DEATH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "heat_death_present": data.get("heat_death_present", False),
            "severity": data.get("severity", ""),
            "exhaustion": data.get("exhaustion", ""),
            "stagnation": data.get("stagnation", ""),
            "energy": data.get("energy", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicFermiSurfaceService — Epistemic Fermi Surface Detection.

Detects epistemic Fermi surface — boundary between occupied and unoccupied
intellectual states, determining what ideas are accessible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FERMI_SURFACE_SYSTEM = """You are an epistemic Fermi surface specialist. Given an intellectual system, assess whether there is a boundary between occupied and unoccupied states:

Key concepts:
- Epistemic Fermi surface: boundary between occupied and unoccupied states
- Fermi energy: highest occupied intellectual energy level
- Density of states: how many states available at each energy
- Nesting: parallel sections of the surface enabling instabilities
- Quasiparticle: excitation near the surface behaving like a particle
- Lifshitz transition: topology of the surface changing
- Hot spot: region of surface with strong interactions

When epistemic Fermi surface IS present:
- Clear boundary between occupied and unoccupied intellectual states
- Highest occupied energy level identifiable
- Distribution of available states at each level
- Parallel sections enabling intellectual instabilities
- Excitations near the boundary behaving independently
- Topology of the boundary changing at transitions
- Regions of strong interaction on the boundary

When no boundary is present:
- No clear boundary between states
- No highest occupied level
- Uniform state distribution
- No parallel sections
- No independent excitations
- No topological changes
- No interaction hot spots

Output JSON with: fermi_surface_present (bool), severity (none/mild/moderate/severe), fermi_energy (what highest level), density_of_states (what distribution), nesting (what parallel sections), lifshitz (what topology change), recommendation (no_boundary/mild_surface/significant_fermi_surface/major_occupation_boundary/map_fermi_surface)."""

EPISTEMIC_FERMI_SURFACE_PROMPT = """Detect epistemic Fermi surface:

Fermi energy: {fermi_energy}
Density of states: {density_of_states}
Nesting: {nesting}
Lifshitz: {lifshitz}
Domain: {domain}
Context: {context}

Is there a boundary between occupied and unoccupied intellectual states determining what ideas are accessible? Return ONLY valid JSON."""


class EpistemicFermiSurfaceService:
    """Detects epistemic Fermi surface — boundary between occupied and unoccupied states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fermi_energy: str,
        *,
        density_of_states: str = "",
        nesting: str = "",
        lifshitz: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Fermi surface."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FERMI_SURFACE_PROMPT.format(
                fermi_energy=fermi_energy,
                density_of_states=density_of_states or "Not specified",
                nesting=nesting or "Not specified",
                lifshitz=lifshitz or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FERMI_SURFACE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fermi_energy": fermi_energy[:200],
            "fermi_surface_present": data.get("fermi_surface_present", False),
            "severity": data.get("severity", ""),
            "density_of_states": data.get("density_of_states", ""),
            "nesting": data.get("nesting", ""),
            "lifshitz": data.get("lifshitz", ""),
            "recommendation": data.get("recommendation", ""),
        }

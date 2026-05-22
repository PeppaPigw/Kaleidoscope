"""EpistemicEnthalpyService — Epistemic Enthalpy Detection.

Detects epistemic enthalpy — the total intellectual energy content of
a system including both internal energy and the work of maintaining structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENTHALPY_SYSTEM = """You are an epistemic enthalpy specialist. Given an intellectual system, assess its total energy content including structural maintenance:

Key concepts:
- Epistemic enthalpy: total energy including structural work
- Internal energy: inherent intellectual content
- PV work: energy maintaining intellectual structure
- Exothermic: releasing energy to environment
- Endothermic: absorbing energy from environment
- Formation enthalpy: energy to create from elements
- Bond energy: energy stored in intellectual connections

When epistemic enthalpy IS present:
- Total energy including structural maintenance costs
- Inherent intellectual content measurable
- Energy spent maintaining intellectual structure
- Releasing energy when ideas combine
- Absorbing energy when ideas form
- Energy required to create from basic elements
- Energy stored in connections between ideas

When energy-free structure is present:
- No energy content to measure
- No inherent intellectual energy
- No structural maintenance cost
- No energy release on combination
- No energy absorption on formation
- No formation energy
- No bond energy

Output JSON with: enthalpy_present (bool), severity (none/mild/moderate/severe), internal_energy (what inherent content), pv_work (what structural cost), exothermic (what energy release), endothermic (what energy absorption), recommendation (energy_free/mild_enthalpy/significant_enthalpy/major_energy_content/optimize_energy_balance)."""

EPISTEMIC_ENTHALPY_PROMPT = """Detect epistemic enthalpy:

Internal energy: {internal_energy}
PV work: {pv_work}
Exothermic: {exothermic}
Endothermic: {endothermic}
Domain: {domain}
Context: {context}

Does this intellectual system have total energy content including both internal energy and the work of maintaining structure? Return ONLY valid JSON."""


class EpistemicEnthalpyService:
    """Detects epistemic enthalpy — total energy including structural work."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        internal_energy: str,
        *,
        pv_work: str = "",
        exothermic: str = "",
        endothermic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic enthalpy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENTHALPY_PROMPT.format(
                internal_energy=internal_energy,
                pv_work=pv_work or "Not specified",
                exothermic=exothermic or "Not specified",
                endothermic=endothermic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENTHALPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "internal_energy": internal_energy[:200],
            "enthalpy_present": data.get("enthalpy_present", False),
            "severity": data.get("severity", ""),
            "pv_work": data.get("pv_work", ""),
            "exothermic": data.get("exothermic", ""),
            "endothermic": data.get("endothermic", ""),
            "recommendation": data.get("recommendation", ""),
        }

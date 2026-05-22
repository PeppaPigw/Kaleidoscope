"""EpistemicGibbsFreeEnergyService — Epistemic Gibbs Free Energy Detection.

Detects epistemic Gibbs free energy — the available intellectual work
that can be extracted from a system at constant temperature and pressure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GIBBS_FREE_ENERGY_SYSTEM = """You are an epistemic Gibbs free energy specialist. Given an intellectual system, assess the available work extractable:

Key concepts:
- Epistemic Gibbs free energy: available intellectual work
- Spontaneity: negative G means process occurs naturally
- Equilibrium: G = 0, no net change possible
- Enthalpy contribution: energy content driving process
- Entropy contribution: disorder driving process
- Temperature dependence: which term dominates
- Coupling: using favorable to drive unfavorable

When epistemic Gibbs free energy IS present:
- Available intellectual work extractable from system
- Processes occurring naturally without external input
- Equilibrium where no further change possible
- Energy content contributing to available work
- Disorder contributing to available work
- Temperature determining which contribution dominates
- Favorable processes driving unfavorable ones

When equilibrium state is present:
- No available work extractable
- No spontaneous processes
- System at equilibrium
- Energy and entropy balanced
- No dominant contribution
- Temperature irrelevant
- No coupling possible

Output JSON with: gibbs_free_energy_present (bool), severity (none/mild/moderate/severe), spontaneity (what natural tendency), equilibrium (what balance point), enthalpy_contribution (what energy drive), entropy_contribution (what disorder drive), recommendation (equilibrium_state/mild_free_energy/significant_gibbs/major_available_work/exploit_spontaneity)."""

EPISTEMIC_GIBBS_FREE_ENERGY_PROMPT = """Detect epistemic Gibbs free energy:

Spontaneity: {spontaneity}
Equilibrium: {equilibrium}
Enthalpy contribution: {enthalpy_contribution}
Entropy contribution: {entropy_contribution}
Domain: {domain}
Context: {context}

Is there available intellectual work that can be extracted from this system? Return ONLY valid JSON."""


class EpistemicGibbsFreeEnergyService:
    """Detects epistemic Gibbs free energy — available intellectual work."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        spontaneity: str,
        *,
        equilibrium: str = "",
        enthalpy_contribution: str = "",
        entropy_contribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Gibbs free energy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GIBBS_FREE_ENERGY_PROMPT.format(
                spontaneity=spontaneity,
                equilibrium=equilibrium or "Not specified",
                enthalpy_contribution=enthalpy_contribution or "Not specified",
                entropy_contribution=entropy_contribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GIBBS_FREE_ENERGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "spontaneity": spontaneity[:200],
            "gibbs_free_energy_present": data.get("gibbs_free_energy_present", False),
            "severity": data.get("severity", ""),
            "equilibrium": data.get("equilibrium", ""),
            "enthalpy_contribution": data.get("enthalpy_contribution", ""),
            "entropy_contribution": data.get("entropy_contribution", ""),
            "recommendation": data.get("recommendation", ""),
        }

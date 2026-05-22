"""EpistemicActivationEnergyService — Epistemic Activation Energy Detection.

Detects epistemic activation energy failure — insufficient energy
to overcome barriers to new understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ACTIVATION_ENERGY_SYSTEM = """You are an epistemic activation energy specialist. Given a knowledge barrier, assess whether insufficient energy prevents new understanding:

Key concepts:
- Epistemic activation energy: energy needed to overcome barriers to understanding
- Barrier height: how much energy is needed to cross
- Insufficient energy: not enough intellectual energy to overcome barrier
- Stuck state: remaining in current understanding due to barrier
- Catalyst absence: no catalyst to lower the barrier
- Transition state: the difficult intermediate state during change
- Energy deficit: gap between available energy and required energy

When activation energy failure IS present:
- Insufficient energy to overcome understanding barriers
- Barriers too high for available intellectual energy
- Stuck in current understanding due to energy deficit
- No catalyst available to lower barriers
- Unable to reach transition state
- Clear gap between available and required energy
- Understanding change blocked by energy barrier

When sufficient energy is present:
- Enough energy to overcome understanding barriers
- Barriers surmountable with available energy
- Able to transition to new understanding
- Catalysts available to lower barriers
- Transition state reachable
- Available energy matches or exceeds requirements
- Understanding change not blocked

Output JSON with: activation_failure (bool), severity (none/mild/moderate/severe), barrier (what barrier exists), energy_available (what energy is available), energy_needed (what energy is needed), catalyst_absent (what catalyst is missing), recommendation (sufficient_energy/mild_deficit/significant_barrier/major_activation_failure/provide_catalyst)."""

EPISTEMIC_ACTIVATION_ENERGY_PROMPT = """Detect epistemic activation energy failure:

Barrier: {barrier}
Energy available: {energy_available}
Energy needed: {energy_needed}
Catalyst absent: {catalyst_absent}
Domain: {domain}
Context: {context}

Is there insufficient energy to overcome barriers to new understanding? Return ONLY valid JSON."""


class EpistemicActivationEnergyService:
    """Detects epistemic activation energy failure — barriers blocking understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        barrier: str,
        *,
        energy_available: str = "",
        energy_needed: str = "",
        catalyst_absent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic activation energy failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ACTIVATION_ENERGY_PROMPT.format(
                barrier=barrier,
                energy_available=energy_available or "Not specified",
                energy_needed=energy_needed or "Not specified",
                catalyst_absent=catalyst_absent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ACTIVATION_ENERGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "barrier": barrier[:200],
            "activation_failure": data.get("activation_failure", False),
            "severity": data.get("severity", ""),
            "energy_available": data.get("energy_available", ""),
            "energy_needed": data.get("energy_needed", ""),
            "catalyst_absent": data.get("catalyst_absent", ""),
            "recommendation": data.get("recommendation", ""),
        }

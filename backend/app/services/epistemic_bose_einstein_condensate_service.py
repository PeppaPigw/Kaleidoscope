"""EpistemicBoseEinsteinCondensateService — Epistemic BEC Detection.

Detects epistemic Bose-Einstein condensate — many ideas collapsing into
the same ground state, losing individual identity in collective behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BEC_SYSTEM = """You are an epistemic Bose-Einstein condensate specialist. Given an intellectual system, assess whether many ideas collapse into the same ground state:

Key concepts:
- Epistemic BEC: many ideas collapsing into same ground state
- Macroscopic occupation: single state holding many ideas
- Coherence: all ideas in phase, acting as one
- Critical temperature: temperature below which condensation occurs
- Superfluidity: frictionless flow of condensed ideas
- Depletion: fraction not in the condensate
- Collective excitation: disturbance of the whole condensate

When epistemic BEC IS present:
- Many ideas collapsing into identical ground state
- Single intellectual state holding disproportionate population
- All condensed ideas coherent and in phase
- Clear threshold below which condensation occurs
- Frictionless flow of condensed intellectual content
- Small fraction remaining outside the condensate
- Disturbances affecting the whole collective

When diverse states is present:
- Ideas distributed across many states
- No single state dominating
- Ideas incoherent and independent
- No condensation threshold
- Normal friction in idea flow
- All ideas independent
- Disturbances remaining local

Output JSON with: bec_present (bool), severity (none/mild/moderate/severe), macroscopic_occupation (what single-state dominance), coherence (what phase alignment), critical_temperature (what threshold), superfluidity (what frictionless flow), recommendation (diverse_states/mild_condensation/significant_bec/major_ground_state_collapse/restore_diversity)."""

EPISTEMIC_BEC_PROMPT = """Detect epistemic Bose-Einstein condensate:

Macroscopic occupation: {macroscopic_occupation}
Coherence: {coherence}
Critical temperature: {critical_temperature}
Superfluidity: {superfluidity}
Domain: {domain}
Context: {context}

Are many ideas collapsing into the same ground state, losing individual identity in collective behavior? Return ONLY valid JSON."""


class EpistemicBoseEinsteinCondensateService:
    """Detects epistemic BEC — many ideas collapsing into same ground state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        macroscopic_occupation: str,
        *,
        coherence: str = "",
        critical_temperature: str = "",
        superfluidity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Bose-Einstein condensate."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BEC_PROMPT.format(
                macroscopic_occupation=macroscopic_occupation,
                coherence=coherence or "Not specified",
                critical_temperature=critical_temperature or "Not specified",
                superfluidity=superfluidity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BEC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "macroscopic_occupation": macroscopic_occupation[:200],
            "bec_present": data.get("bec_present", False),
            "severity": data.get("severity", ""),
            "coherence": data.get("coherence", ""),
            "critical_temperature": data.get("critical_temperature", ""),
            "superfluidity": data.get("superfluidity", ""),
            "recommendation": data.get("recommendation", ""),
        }

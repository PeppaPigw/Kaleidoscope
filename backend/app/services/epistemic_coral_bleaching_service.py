"""EpistemicCoralBleachingService — Epistemic Coral Bleaching Detection.

Detects epistemic coral bleaching — rich intellectual ecosystems
losing their symbiotic relationships and becoming barren.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CORAL_BLEACHING_SYSTEM = """You are an epistemic coral bleaching specialist. Given an intellectual ecosystem, assess whether symbiotic relationships are being lost:

Key concepts:
- Epistemic coral bleaching: rich ecosystems losing symbiotic relationships
- Symbiosis loss: mutually beneficial intellectual relationships dying
- Stress response: ecosystem responding to intellectual stress
- Bleaching: loss of color/vitality from knowledge structures
- Recovery potential: whether the ecosystem can recover
- Cascade failure: one loss triggering others
- Reef death: complete loss of intellectual ecosystem

When epistemic coral bleaching IS present:
- Rich intellectual ecosystems losing their vitality
- Mutually beneficial relationships between ideas dying
- Ecosystem responding to intellectual stress by shedding connections
- Knowledge structures losing their color and vitality
- Uncertain whether the ecosystem can recover
- One relationship loss triggering cascade of others
- Risk of complete intellectual ecosystem death

When thriving ecosystem is present:
- Rich intellectual ecosystems maintaining vitality
- Mutually beneficial relationships thriving
- Ecosystem resilient to intellectual stress
- Knowledge structures vibrant and vital
- Ecosystem robust and self-sustaining
- Relationships reinforcing each other
- No risk of ecosystem collapse

Output JSON with: bleaching_present (bool), severity (none/mild/moderate/severe), ecosystem (what ecosystem bleaches), symbiosis_loss (what relationships die), stress (what stress causes it), recovery (whether recovery is possible), recommendation (thriving_ecosystem/mild_stress/significant_bleaching/major_ecosystem_death/reduce_stress_restore_symbiosis)."""

EPISTEMIC_CORAL_BLEACHING_PROMPT = """Detect epistemic coral bleaching:

Ecosystem: {ecosystem}
Symbiosis loss: {symbiosis_loss}
Stress: {stress}
Recovery: {recovery}
Domain: {domain}
Context: {context}

Is a rich intellectual ecosystem losing its symbiotic relationships and becoming barren? Return ONLY valid JSON."""


class EpistemicCoralBleachingService:
    """Detects epistemic coral bleaching — intellectual ecosystem losing vitality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        symbiosis_loss: str = "",
        stress: str = "",
        recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic coral bleaching."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CORAL_BLEACHING_PROMPT.format(
                ecosystem=ecosystem,
                symbiosis_loss=symbiosis_loss or "Not specified",
                stress=stress or "Not specified",
                recovery=recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CORAL_BLEACHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "bleaching_present": data.get("bleaching_present", False),
            "severity": data.get("severity", ""),
            "symbiosis_loss": data.get("symbiosis_loss", ""),
            "stress": data.get("stress", ""),
            "recovery": data.get("recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }

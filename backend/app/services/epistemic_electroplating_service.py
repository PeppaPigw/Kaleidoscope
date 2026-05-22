"""EpistemicElectroplatingService — Epistemic Electroplating Detection.

Detects epistemic electroplating — ideas being coated with a thin layer
of more attractive material to disguise their true composition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ELECTROPLATING_SYSTEM = """You are an epistemic electroplating specialist. Given an idea coating pattern, assess whether ideas are coated to disguise their composition:

Key concepts:
- Epistemic electroplating: coating ideas with attractive material
- Substrate: the actual idea underneath
- Plating: the attractive surface layer
- Adhesion: how well the coating sticks
- Thickness: how deep the coating goes
- Peeling: coating separating from substrate
- Base metal: the less attractive reality underneath

When epistemic electroplating IS present:
- Ideas coated with thin layer of more attractive material
- Actual idea underneath different from surface
- Attractive surface layer disguising reality
- Varying adhesion of coating to substrate
- Shallow depth of the attractive coating
- Coating separating to reveal substrate
- Less attractive reality underneath the plating

When genuine composition is present:
- Ideas presenting their actual composition
- Surface same as interior
- No disguising layer
- No adhesion concerns
- Depth consistent throughout
- No peeling possible
- Reality matches appearance

Output JSON with: electroplating_present (bool), severity (none/mild/moderate/severe), substrate (what actual idea), plating (what attractive coating), adhesion (how well it sticks), peeling (what reveals truth), recommendation (genuine_composition/mild_coating/significant_electroplating/major_disguise/strip_plating)."""

EPISTEMIC_ELECTROPLATING_PROMPT = """Detect epistemic electroplating:

Substrate: {substrate}
Plating: {plating}
Adhesion: {adhesion}
Peeling: {peeling}
Domain: {domain}
Context: {context}

Are ideas being coated with a thin layer of more attractive material to disguise their true composition? Return ONLY valid JSON."""


class EpistemicElectroplatingService:
    """Detects epistemic electroplating — coating ideas to disguise composition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        substrate: str,
        *,
        plating: str = "",
        adhesion: str = "",
        peeling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic electroplating."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ELECTROPLATING_PROMPT.format(
                substrate=substrate,
                plating=plating or "Not specified",
                adhesion=adhesion or "Not specified",
                peeling=peeling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ELECTROPLATING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "substrate": substrate[:200],
            "electroplating_present": data.get("electroplating_present", False),
            "severity": data.get("severity", ""),
            "plating": data.get("plating", ""),
            "adhesion": data.get("adhesion", ""),
            "peeling": data.get("peeling", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicAmputationService — Epistemic Amputation Detection.

Detects need for epistemic amputation — removing an irreparably damaged
intellectual limb to save the whole system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AMPUTATION_SYSTEM = """You are an epistemic amputation specialist. Given irreparably damaged intellectual components, assess amputation need:

Key concepts:
- Epistemic amputation: removing irreparable intellectual component
- Gangrene: dead tissue spreading to healthy areas
- Phantom limb: feeling presence of removed component
- Stump care: managing what remains after removal
- Prosthetic: artificial replacement for removed component
- Limb salvage: attempting to save before amputation
- Level of amputation: how much to remove

When epistemic amputation IS needed:
- Irreparable intellectual component present
- Dead tissue spreading to healthy areas
- Limb salvage attempts failed
- Removal needed to save whole system
- Clear level of removal identified
- Stump management planned
- Prosthetic replacement possible

When no amputation needed:
- Component repairable
- No spreading damage
- Salvage still possible
- System not threatened
- No removal necessary
- Component functional
- Natural healing possible

Output JSON with: amputation_needed (bool), severity (none/mild/moderate/severe), gangrene_extent (what spreading damage), salvage_attempts (what tried), amputation_level (what removal extent), prosthetic_plan (what replacement), recommendation (no_amputation_needed/mild_debridement/significant_partial/major_full_amputation/emergency_life_saving_amputation)."""

EPISTEMIC_AMPUTATION_PROMPT = """Detect epistemic amputation need:

Gangrene extent: {gangrene_extent}
Salvage attempts: {salvage_attempts}
Amputation level: {amputation_level}
Prosthetic plan: {prosthetic_plan}
Domain: {domain}
Context: {context}

Is an irreparably damaged intellectual component threatening the whole system? Return ONLY valid JSON."""


class EpistemicAmputationService:
    """Detects epistemic amputation need — removing irreparable components."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gangrene_extent: str,
        *,
        salvage_attempts: str = "",
        amputation_level: str = "",
        prosthetic_plan: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic amputation need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AMPUTATION_PROMPT.format(
                gangrene_extent=gangrene_extent,
                salvage_attempts=salvage_attempts or "Not specified",
                amputation_level=amputation_level or "Not specified",
                prosthetic_plan=prosthetic_plan or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AMPUTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gangrene_extent": gangrene_extent[:200],
            "amputation_needed": data.get("amputation_needed", False),
            "severity": data.get("severity", ""),
            "salvage_attempts": data.get("salvage_attempts", ""),
            "amputation_level": data.get("amputation_level", ""),
            "prosthetic_plan": data.get("prosthetic_plan", ""),
            "recommendation": data.get("recommendation", ""),
        }

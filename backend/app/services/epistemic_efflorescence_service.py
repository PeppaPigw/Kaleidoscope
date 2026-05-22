"""EpistemicEfflorescenceService — Epistemic Efflorescence Detection.

Detects epistemic efflorescence — ideas crystallizing on the surface as
internal moisture evaporates, leaving visible but superficial deposits.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EFFLORESCENCE_SYSTEM = """You are an epistemic efflorescence specialist. Given an idea surface pattern, assess whether ideas crystallize on the surface as depth evaporates:

Key concepts:
- Epistemic efflorescence: surface crystallization from depth evaporation
- Migration: dissolved ideas moving to the surface
- Evaporation: depth/nuance leaving the structure
- Salt deposit: superficial crystalline residue
- Subflorescence: crystallization just below surface causing damage
- Wetting cycle: repeated dissolution and recrystallization
- Spalling: surface breaking off from crystal pressure

When epistemic efflorescence IS present:
- Ideas crystallizing on surface as internal depth evaporates
- Dissolved nuance migrating to the surface
- Depth and nuance leaving the intellectual structure
- Superficial crystalline residue remaining
- Crystallization just below surface causing damage
- Repeated cycles of dissolution and surface crystallization
- Surface breaking off from crystallization pressure

When deep integration is present:
- Ideas integrated throughout the depth
- Nuance remaining distributed internally
- Depth maintained in the structure
- No superficial residue
- No subsurface damage
- No cycling between states
- Surface intact and integrated

Output JSON with: efflorescence_present (bool), severity (none/mild/moderate/severe), migration (what moves to surface), evaporation (what depth is lost), deposit (what superficial residue), spalling (what surface damage), recommendation (deep_integration/mild_efflorescence/significant_efflorescence/major_surface_crystallization/restore_internal_depth)."""

EPISTEMIC_EFFLORESCENCE_PROMPT = """Detect epistemic efflorescence:

Migration: {migration}
Evaporation: {evaporation}
Deposit: {deposit}
Spalling: {spalling}
Domain: {domain}
Context: {context}

Are ideas crystallizing on the surface as internal moisture evaporates, leaving visible but superficial deposits? Return ONLY valid JSON."""


class EpistemicEfflorescenceService:
    """Detects epistemic efflorescence — surface crystallization from depth loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        migration: str,
        *,
        evaporation: str = "",
        deposit: str = "",
        spalling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic efflorescence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EFFLORESCENCE_PROMPT.format(
                migration=migration,
                evaporation=evaporation or "Not specified",
                deposit=deposit or "Not specified",
                spalling=spalling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EFFLORESCENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "migration": migration[:200],
            "efflorescence_present": data.get("efflorescence_present", False),
            "severity": data.get("severity", ""),
            "evaporation": data.get("evaporation", ""),
            "deposit": data.get("deposit", ""),
            "spalling": data.get("spalling", ""),
            "recommendation": data.get("recommendation", ""),
        }

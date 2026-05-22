"""EpistemicKidneyStoneService — Epistemic Kidney Stone Detection.

Detects epistemic kidney stones — crystallized deposits blocking
intellectual filtration pathways, causing acute obstruction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KIDNEY_STONE_SYSTEM = """You are an epistemic kidney stone specialist. Given intellectual filtration pathways, assess whether crystallized deposits are causing obstruction:

Key concepts:
- Epistemic kidney stone: crystallized deposit blocking filtration pathway
- Nucleation: initial crystal formation from supersaturated solution
- Obstruction: blockage of flow by the stone
- Hydronephrosis: backup pressure from obstruction
- Colic: acute pain from stone movement
- Lithotripsy: breaking stones into passable fragments
- Supersaturation: conditions allowing crystal formation

When epistemic kidney stones ARE present:
- Crystallized deposits blocking filtration pathways
- Initial crystal formation from concentrated ideas
- Blockage of intellectual flow by deposits
- Backup pressure from obstruction
- Acute disruption from stone movement
- Need to break deposits into passable fragments
- Conditions allowing crystal formation

When healthy pathways are present:
- No crystallized deposits
- No crystal formation
- No flow blockage
- No backup pressure
- No acute disruption
- No fragmentation needed
- Dilute conditions preventing crystals

Output JSON with: kidney_stone_present (bool), severity (none/mild/moderate/severe), nucleation (what crystal formation), obstruction (what flow blockage), hydronephrosis (what backup pressure), supersaturation (what concentration conditions), recommendation (healthy_pathways/mild_stone/significant_kidney_stone/major_obstruction/dissolve_intellectual_deposits)."""

EPISTEMIC_KIDNEY_STONE_PROMPT = """Detect epistemic kidney stone:

Nucleation: {nucleation}
Obstruction: {obstruction}
Hydronephrosis: {hydronephrosis}
Supersaturation: {supersaturation}
Domain: {domain}
Context: {context}

Are crystallized deposits blocking intellectual filtration pathways? Return ONLY valid JSON."""


class EpistemicKidneyStoneService:
    """Detects epistemic kidney stones — crystallized deposits blocking pathways."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nucleation: str,
        *,
        obstruction: str = "",
        hydronephrosis: str = "",
        supersaturation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic kidney stone."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KIDNEY_STONE_PROMPT.format(
                nucleation=nucleation,
                obstruction=obstruction or "Not specified",
                hydronephrosis=hydronephrosis or "Not specified",
                supersaturation=supersaturation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KIDNEY_STONE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nucleation": nucleation[:200],
            "kidney_stone_present": data.get("kidney_stone_present", False),
            "severity": data.get("severity", ""),
            "obstruction": data.get("obstruction", ""),
            "hydronephrosis": data.get("hydronephrosis", ""),
            "supersaturation": data.get("supersaturation", ""),
            "recommendation": data.get("recommendation", ""),
        }

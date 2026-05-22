"""EpistemicGallingService — Epistemic Galling Detection.

Detects epistemic galling — ideas seizing together under pressure,
transferring material between surfaces and creating permanent damage.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GALLING_SYSTEM = """You are an epistemic galling specialist. Given an idea seizure pattern, assess whether ideas seize together under pressure:

Key concepts:
- Epistemic galling: ideas seizing together under pressure
- Cold welding: surfaces bonding under pressure without heat
- Material transfer: one surface depositing on another
- Seizure: complete locking of surfaces together
- Surface finish: roughness affecting galling tendency
- Dissimilar materials: different ideas less likely to gall
- Anti-gall coating: protective layer preventing seizure

When epistemic galling IS present:
- Ideas seizing together under pressure
- Surfaces bonding under pressure without deliberate joining
- One idea depositing material on another
- Complete locking of ideas together
- Surface roughness affecting seizure tendency
- Similar ideas more likely to seize together
- Need for protective layers to prevent seizure

When free sliding is present:
- Ideas moving freely past each other
- No bonding under pressure
- No material transfer between ideas
- No locking together
- Surface finish not affecting interaction
- Similar ideas not seizing
- No protective layers needed

Output JSON with: galling_present (bool), severity (none/mild/moderate/severe), cold_welding (what bonds under pressure), material_transfer (what deposits where), seizure (what locks together), anti_gall (what prevents seizure), recommendation (free_sliding/mild_galling/significant_galling/major_seizure/apply_anti_gall_coating)."""

EPISTEMIC_GALLING_PROMPT = """Detect epistemic galling:

Cold welding: {cold_welding}
Material transfer: {material_transfer}
Seizure: {seizure}
Anti-gall: {anti_gall}
Domain: {domain}
Context: {context}

Are ideas seizing together under pressure, transferring material between surfaces and creating permanent damage? Return ONLY valid JSON."""


class EpistemicGallingService:
    """Detects epistemic galling — ideas seizing together under pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cold_welding: str,
        *,
        material_transfer: str = "",
        seizure: str = "",
        anti_gall: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic galling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GALLING_PROMPT.format(
                cold_welding=cold_welding,
                material_transfer=material_transfer or "Not specified",
                seizure=seizure or "Not specified",
                anti_gall=anti_gall or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GALLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cold_welding": cold_welding[:200],
            "galling_present": data.get("galling_present", False),
            "severity": data.get("severity", ""),
            "material_transfer": data.get("material_transfer", ""),
            "seizure": data.get("seizure", ""),
            "anti_gall": data.get("anti_gall", ""),
            "recommendation": data.get("recommendation", ""),
        }

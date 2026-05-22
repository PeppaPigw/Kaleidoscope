"""EpistemicRootCanalService — Epistemic Root Canal Detection.

Detects need for epistemic root canal — removing infected intellectual
pulp from deep within a concept while preserving the outer structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ROOT_CANAL_SYSTEM = """You are an epistemic root canal specialist. Given infected intellectual core, assess root canal need:

Key concepts:
- Epistemic root canal: removing infected core while preserving structure
- Pulpitis: inflammation of intellectual core
- Periapical abscess: infection at root tip
- Obturation: filling empty canal after removal
- Crown restoration: rebuilding outer structure after
- Vital pulp: still-living core tissue
- Necrotic pulp: dead core tissue

When epistemic root canal IS needed:
- Infected intellectual core present
- Core inflammation causing pain
- Infection at root tip
- Need to fill after removal
- Outer structure worth preserving
- Core tissue dying or dead
- Deep infection unreachable by surface treatment

When no root canal needed:
- Healthy intellectual core
- No core inflammation
- No root infection
- No filling needed
- Structure intact
- Core tissue vital and healthy
- Surface treatment sufficient

Output JSON with: root_canal_needed (bool), severity (none/mild/moderate/severe), pulp_status (what core condition), infection_extent (what spread), preservation_value (what structure worth), obturation_plan (what filling approach), recommendation (no_root_canal/mild_pulp_capping/significant_pulpotomy/major_full_root_canal/emergency_incision_drainage)."""

EPISTEMIC_ROOT_CANAL_PROMPT = """Detect epistemic root canal need:

Pulp status: {pulp_status}
Infection extent: {infection_extent}
Preservation value: {preservation_value}
Obturation plan: {obturation_plan}
Domain: {domain}
Context: {context}

Is there infected intellectual core needing removal while preserving outer structure? Return ONLY valid JSON."""


class EpistemicRootCanalService:
    """Detects epistemic root canal need — removing infected core preserving structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pulp_status: str,
        *,
        infection_extent: str = "",
        preservation_value: str = "",
        obturation_plan: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic root canal need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ROOT_CANAL_PROMPT.format(
                pulp_status=pulp_status,
                infection_extent=infection_extent or "Not specified",
                preservation_value=preservation_value or "Not specified",
                obturation_plan=obturation_plan or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ROOT_CANAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pulp_status": pulp_status[:200],
            "root_canal_needed": data.get("root_canal_needed", False),
            "severity": data.get("severity", ""),
            "infection_extent": data.get("infection_extent", ""),
            "preservation_value": data.get("preservation_value", ""),
            "obturation_plan": data.get("obturation_plan", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicDrainageService — Epistemic Drainage Detection.

Detects need for epistemic drainage — removing accumulated intellectual
fluid or pus that is causing pressure and preventing healing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DRAINAGE_SYSTEM = """You are an epistemic drainage specialist. Given intellectual fluid accumulation, assess drainage need:

Key concepts:
- Epistemic drainage: removing accumulated intellectual fluid
- Abscess: walled-off collection of intellectual pus
- Effusion: fluid accumulation in intellectual space
- Empyema: infected fluid collection
- Compartment syndrome: pressure from fluid buildup
- Incision and drainage: surgical opening to release
- Percutaneous drainage: needle-guided removal

When epistemic drainage IS needed:
- Accumulated intellectual fluid present
- Walled-off collection forming
- Fluid in intellectual spaces
- Infected collection present
- Pressure from buildup causing damage
- Surgical opening needed
- Guided removal required

When no drainage needed:
- No fluid accumulation
- No collections present
- Spaces clear
- No infection
- No pressure buildup
- No opening needed
- Self-resolving

Output JSON with: drainage_needed (bool), severity (none/mild/moderate/severe), collection_type (what accumulation), pressure_status (what buildup), infection_signs (what contamination), drainage_method (what removal approach), recommendation (no_drainage_needed/mild_aspiration/significant_drainage/major_surgical_drainage/emergency_decompression)."""

EPISTEMIC_DRAINAGE_PROMPT = """Detect epistemic drainage need:

Collection type: {collection_type}
Pressure status: {pressure_status}
Infection signs: {infection_signs}
Drainage method: {drainage_method}
Domain: {domain}
Context: {context}

Is accumulated intellectual fluid causing pressure and preventing healing? Return ONLY valid JSON."""


class EpistemicDrainageService:
    """Detects epistemic drainage need — removing accumulated intellectual fluid."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        collection_type: str,
        *,
        pressure_status: str = "",
        infection_signs: str = "",
        drainage_method: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic drainage need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DRAINAGE_PROMPT.format(
                collection_type=collection_type,
                pressure_status=pressure_status or "Not specified",
                infection_signs=infection_signs or "Not specified",
                drainage_method=drainage_method or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DRAINAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "collection_type": collection_type[:200],
            "drainage_needed": data.get("drainage_needed", False),
            "severity": data.get("severity", ""),
            "pressure_status": data.get("pressure_status", ""),
            "infection_signs": data.get("infection_signs", ""),
            "drainage_method": data.get("drainage_method", ""),
            "recommendation": data.get("recommendation", ""),
        }

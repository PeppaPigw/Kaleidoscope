"""EpistemicBileDuctObstructionService — Epistemic Bile Duct Obstruction Detection.

Detects epistemic bile duct obstruction — blocked channels preventing
the export of intellectual waste products from the processing system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BILE_DUCT_OBSTRUCTION_SYSTEM = """You are an epistemic bile duct obstruction specialist. Given intellectual waste export channels, assess whether they are blocked:

Key concepts:
- Epistemic bile duct obstruction: blocked channels preventing waste export
- Cholestasis: bile/waste flow stoppage
- Jaundice: waste products backing up into system
- Gallstone: solid mass blocking the duct
- Stricture: narrowing of the export channel
- Biliary pressure: buildup behind the blockage
- Decompression: relieving the obstruction

When epistemic bile duct obstruction IS present:
- Blocked channels preventing waste export
- Waste flow completely stopped
- Waste products backing up into the system
- Solid masses blocking export ducts
- Export channels narrowed
- Pressure building behind blockages
- Need for decompression interventions

When healthy export is present:
- Clear export channels
- Normal waste flow
- No backup of waste
- No blocking masses
- Full channel diameter
- No pressure buildup
- No decompression needed

Output JSON with: bile_duct_obstruction_present (bool), severity (none/mild/moderate/severe), cholestasis (what flow stoppage), jaundice (what waste backup), gallstone (what blocking mass), stricture (what channel narrowing), recommendation (healthy_export/mild_obstruction/significant_bile_duct_obstruction/major_waste_blockage/clear_export_channels)."""

EPISTEMIC_BILE_DUCT_OBSTRUCTION_PROMPT = """Detect epistemic bile duct obstruction:

Cholestasis: {cholestasis}
Jaundice: {jaundice}
Gallstone: {gallstone}
Stricture: {stricture}
Domain: {domain}
Context: {context}

Are blocked channels preventing the export of intellectual waste products? Return ONLY valid JSON."""


class EpistemicBileDuctObstructionService:
    """Detects epistemic bile duct obstruction — blocked waste export channels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cholestasis: str,
        *,
        jaundice: str = "",
        gallstone: str = "",
        stricture: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bile duct obstruction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BILE_DUCT_OBSTRUCTION_PROMPT.format(
                cholestasis=cholestasis,
                jaundice=jaundice or "Not specified",
                gallstone=gallstone or "Not specified",
                stricture=stricture or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BILE_DUCT_OBSTRUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cholestasis": cholestasis[:200],
            "bile_duct_obstruction_present": data.get("bile_duct_obstruction_present", False),
            "severity": data.get("severity", ""),
            "jaundice": data.get("jaundice", ""),
            "gallstone": data.get("gallstone", ""),
            "stricture": data.get("stricture", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicRefluxService — Epistemic Reflux Detection.

Detects epistemic reflux — intellectual acid flowing backward from
processing into intake, causing burning and damage to input channels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REFLUX_SYSTEM = """You are an epistemic reflux specialist. Given intellectual acid flowing backward, assess reflux:

Key concepts:
- Epistemic reflux: processed material flowing backward into intake
- Heartburn: burning sensation from acid in wrong location
- Sphincter incompetence: valve between intake and processing failing
- Barrett's: chronic damage transforming tissue type
- Proton pump inhibitor: reducing acid production
- Lifestyle modification: changing intake patterns
- Erosive: causing visible damage to intake lining

When epistemic reflux IS present:
- Processed material flowing backward
- Burning from acid in wrong location
- Valve between intake and processing failing
- Chronic damage transforming tissue
- Acid production excessive
- Intake patterns problematic
- Visible damage to intake lining

When no reflux:
- Normal forward flow maintained
- No burning sensation
- Valve functioning properly
- No tissue transformation
- Normal acid levels
- Healthy intake patterns
- Intake lining intact

Output JSON with: reflux_detected (bool), severity (none/mild/moderate/severe), flow_direction (what backward movement), sphincter_status (what valve function), damage_extent (what erosion), acid_level (what production), recommendation (no_reflux/mild_lifestyle/significant_acid_suppression/major_surgical_repair/emergency_stricture)."""

EPISTEMIC_REFLUX_PROMPT = """Detect epistemic reflux:

Flow direction: {flow_direction}
Sphincter status: {sphincter_status}
Damage extent: {damage_extent}
Acid level: {acid_level}
Domain: {domain}
Context: {context}

Is intellectual acid flowing backward from processing into intake causing damage? Return ONLY valid JSON."""


class EpistemicRefluxService:
    """Detects epistemic reflux — processed material flowing backward."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow_direction: str,
        *,
        sphincter_status: str = "",
        damage_extent: str = "",
        acid_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reflux."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REFLUX_PROMPT.format(
                flow_direction=flow_direction,
                sphincter_status=sphincter_status or "Not specified",
                damage_extent=damage_extent or "Not specified",
                acid_level=acid_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REFLUX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow_direction": flow_direction[:200],
            "reflux_detected": data.get("reflux_detected", False),
            "severity": data.get("severity", ""),
            "sphincter_status": data.get("sphincter_status", ""),
            "damage_extent": data.get("damage_extent", ""),
            "acid_level": data.get("acid_level", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicBypassSurgeryService — Epistemic Bypass Surgery Detection.

Detects need for epistemic bypass surgery — creating alternative pathways
around blocked intellectual channels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BYPASS_SURGERY_SYSTEM = """You are an epistemic bypass surgery specialist. Given blocked intellectual channels, assess bypass need:

Key concepts:
- Epistemic bypass: creating alternative pathway around blockage
- Stenosis: narrowing of intellectual channel
- Occlusion: complete blockage of channel
- Collateral circulation: natural alternative pathways
- Graft conduit: material used to create bypass
- Anastomosis: connection point of new pathway
- Patency: whether bypass remains open

When epistemic bypass surgery IS needed:
- Intellectual channel blocked or narrowed
- Complete occlusion present
- Natural alternatives insufficient
- Graft material available
- Connection points identifiable
- Reasonable patency expected
- Flow restoration critical

When no bypass needed:
- Channels open and flowing
- No significant narrowing
- Natural alternatives adequate
- No blockage present
- Normal flow maintained
- No intervention needed
- Self-clearing possible

Output JSON with: bypass_needed (bool), severity (none/mild/moderate/severe), stenosis_degree (what narrowing), occlusion_type (what blockage), collateral_status (what natural alternatives), graft_plan (what conduit approach), recommendation (no_bypass_needed/mild_angioplasty/significant_single_bypass/major_multi_vessel/emergency_urgent_bypass)."""

EPISTEMIC_BYPASS_SURGERY_PROMPT = """Detect epistemic bypass surgery need:

Stenosis degree: {stenosis_degree}
Occlusion type: {occlusion_type}
Collateral status: {collateral_status}
Graft plan: {graft_plan}
Domain: {domain}
Context: {context}

Are intellectual channels blocked requiring alternative pathway creation? Return ONLY valid JSON."""


class EpistemicBypassSurgeryService:
    """Detects epistemic bypass surgery need — creating alternative pathways."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stenosis_degree: str,
        *,
        occlusion_type: str = "",
        collateral_status: str = "",
        graft_plan: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bypass surgery need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BYPASS_SURGERY_PROMPT.format(
                stenosis_degree=stenosis_degree,
                occlusion_type=occlusion_type or "Not specified",
                collateral_status=collateral_status or "Not specified",
                graft_plan=graft_plan or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BYPASS_SURGERY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stenosis_degree": stenosis_degree[:200],
            "bypass_needed": data.get("bypass_needed", False),
            "severity": data.get("severity", ""),
            "occlusion_type": data.get("occlusion_type", ""),
            "collateral_status": data.get("collateral_status", ""),
            "graft_plan": data.get("graft_plan", ""),
            "recommendation": data.get("recommendation", ""),
        }

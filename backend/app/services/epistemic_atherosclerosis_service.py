"""EpistemicAtherosclerosisService — Epistemic Atherosclerosis Detection.

Detects epistemic atherosclerosis — gradual buildup of deposits that narrow
intellectual channels, restricting the flow of ideas over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATHEROSCLEROSIS_SYSTEM = """You are an epistemic atherosclerosis specialist. Given intellectual channels, assess whether gradual buildup is narrowing idea flow:

Key concepts:
- Epistemic atherosclerosis: gradual buildup narrowing intellectual channels
- Plaque formation: deposits accumulating on channel walls
- Stenosis: progressive narrowing of the channel
- Ischemia: insufficient flow to downstream areas
- Calcification: hardening of deposits making them permanent
- Collateral circulation: alternative pathways developing
- Thrombosis: sudden blockage from plaque rupture

When epistemic atherosclerosis IS present:
- Gradual buildup narrowing intellectual channels
- Deposits accumulating on communication pathways
- Progressive narrowing of idea flow channels
- Insufficient flow reaching downstream areas
- Deposits hardening and becoming permanent
- Alternative pathways developing around blockages
- Risk of sudden complete blockage

When healthy channels are present:
- Clear open intellectual channels
- No deposit accumulation
- Full channel diameter maintained
- Adequate flow to all areas
- Flexible channel walls
- No need for alternative routes
- No blockage risk

Output JSON with: atherosclerosis_present (bool), severity (none/mild/moderate/severe), plaque_formation (what deposit buildup), stenosis (what narrowing), ischemia (what insufficient flow), calcification (what hardening), recommendation (healthy_channels/mild_atherosclerosis/significant_atherosclerosis/major_channel_narrowing/clear_intellectual_channels)."""

EPISTEMIC_ATHEROSCLEROSIS_PROMPT = """Detect epistemic atherosclerosis:

Plaque formation: {plaque_formation}
Stenosis: {stenosis}
Ischemia: {ischemia}
Calcification: {calcification}
Domain: {domain}
Context: {context}

Is gradual buildup narrowing intellectual channels and restricting idea flow? Return ONLY valid JSON."""


class EpistemicAtherosclerosisService:
    """Detects epistemic atherosclerosis — gradual narrowing of intellectual channels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        plaque_formation: str,
        *,
        stenosis: str = "",
        ischemia: str = "",
        calcification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic atherosclerosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATHEROSCLEROSIS_PROMPT.format(
                plaque_formation=plaque_formation,
                stenosis=stenosis or "Not specified",
                ischemia=ischemia or "Not specified",
                calcification=calcification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATHEROSCLEROSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "plaque_formation": plaque_formation[:200],
            "atherosclerosis_present": data.get("atherosclerosis_present", False),
            "severity": data.get("severity", ""),
            "stenosis": data.get("stenosis", ""),
            "ischemia": data.get("ischemia", ""),
            "calcification": data.get("calcification", ""),
            "recommendation": data.get("recommendation", ""),
        }

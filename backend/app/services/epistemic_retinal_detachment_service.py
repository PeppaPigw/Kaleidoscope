"""EpistemicRetinalDetachmentService — Epistemic Retinal Detachment Detection.

Detects epistemic retinal detachment — separation of the perception layer
from its supporting structure, causing loss of intellectual vision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RETINAL_DETACHMENT_SYSTEM = """You are an epistemic retinal detachment specialist. Given intellectual perception layers, assess whether separation from support is occurring:

Key concepts:
- Epistemic retinal detachment: perception layer separating from support
- Rhegmatogenous: tear allowing fluid under perception layer
- Tractional: pulling forces separating layers
- Exudative: fluid accumulation pushing layers apart
- Floaters: debris from separation visible in field
- Curtain effect: progressive loss of visual field
- Reattachment: surgical restoration of layer contact

When epistemic retinal detachment IS present:
- Perception layer separating from supporting structure
- Tears allowing interference under perception
- Pulling forces separating intellectual layers
- Fluid accumulation pushing layers apart
- Debris from separation visible in intellectual field
- Progressive loss of intellectual visual field
- Need for surgical restoration of contact

When healthy attachment is present:
- Perception layer firmly attached to support
- No tears in perception layer
- No tractional forces
- No fluid accumulation between layers
- No floaters or debris
- Full visual field maintained
- No reattachment needed

Output JSON with: retinal_detachment_present (bool), severity (none/mild/moderate/severe), rhegmatogenous (what tear-based separation), tractional (what pulling forces), curtain_effect (what progressive field loss), floaters (what visible debris), recommendation (healthy_attachment/mild_detachment/significant_retinal_detachment/major_layer_separation/reattach_perception_layer)."""

EPISTEMIC_RETINAL_DETACHMENT_PROMPT = """Detect epistemic retinal detachment:

Rhegmatogenous: {rhegmatogenous}
Tractional: {tractional}
Curtain effect: {curtain_effect}
Floaters: {floaters}
Domain: {domain}
Context: {context}

Is the perception layer separating from its supporting structure? Return ONLY valid JSON."""


class EpistemicRetinalDetachmentService:
    """Detects epistemic retinal detachment — perception separating from support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rhegmatogenous: str,
        *,
        tractional: str = "",
        curtain_effect: str = "",
        floaters: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic retinal detachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RETINAL_DETACHMENT_PROMPT.format(
                rhegmatogenous=rhegmatogenous,
                tractional=tractional or "Not specified",
                curtain_effect=curtain_effect or "Not specified",
                floaters=floaters or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RETINAL_DETACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rhegmatogenous": rhegmatogenous[:200],
            "retinal_detachment_present": data.get("retinal_detachment_present", False),
            "severity": data.get("severity", ""),
            "tractional": data.get("tractional", ""),
            "curtain_effect": data.get("curtain_effect", ""),
            "floaters": data.get("floaters", ""),
            "recommendation": data.get("recommendation", ""),
        }

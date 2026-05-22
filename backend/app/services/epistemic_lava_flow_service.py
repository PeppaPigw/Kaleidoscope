"""EpistemicLavaFlowService — Epistemic Lava Flow Detection.

Detects epistemic lava flows — slow-moving but unstoppable intellectual
forces that bury existing knowledge under new layers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LAVA_FLOW_SYSTEM = """You are an epistemic lava flow specialist. Given an intellectual force, assess whether slow unstoppable forces are burying existing knowledge:

Key concepts:
- Epistemic lava flow: slow but unstoppable intellectual force
- Burial: existing knowledge buried under new layers
- Viscosity: how thick and slow the flow moves
- Front: advancing edge of the flow
- Cooling: flow eventually solidifying into new ground
- Diversion: attempts to redirect the flow
- Stratigraphy: layers of buried knowledge beneath

When epistemic lava flow IS present:
- Slow-moving but unstoppable intellectual forces
- Existing knowledge being buried under new layers
- Thick slow-moving intellectual material advancing
- Clear advancing edge of the intellectual force
- Flow eventually solidifying into new intellectual ground
- Attempts to redirect the flow largely failing
- Layers of buried knowledge accumulating beneath

When open landscape is present:
- No unstoppable forces burying knowledge
- Existing knowledge remaining accessible
- No thick material advancing
- No advancing front threatening knowledge
- No solidification of new layers over old
- Intellectual forces redirectable
- All knowledge layers accessible

Output JSON with: lava_flow_present (bool), severity (none/mild/moderate/severe), flow (what unstoppable force advances), burial (what knowledge is buried), viscosity (how thick and slow), cooling (what solidifies), recommendation (open_landscape/mild_flow/significant_burial/major_unstoppable_force/divert_or_preserve_before_burial)."""

EPISTEMIC_LAVA_FLOW_PROMPT = """Detect epistemic lava flow:

Flow: {flow}
Burial: {burial}
Viscosity: {viscosity}
Cooling: {cooling}
Domain: {domain}
Context: {context}

Are slow but unstoppable intellectual forces burying existing knowledge under new layers? Return ONLY valid JSON."""


class EpistemicLavaFlowService:
    """Detects epistemic lava flows — slow unstoppable forces burying knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow: str,
        *,
        burial: str = "",
        viscosity: str = "",
        cooling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lava flow."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LAVA_FLOW_PROMPT.format(
                flow=flow,
                burial=burial or "Not specified",
                viscosity=viscosity or "Not specified",
                cooling=cooling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LAVA_FLOW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow": flow[:200],
            "lava_flow_present": data.get("lava_flow_present", False),
            "severity": data.get("severity", ""),
            "burial": data.get("burial", ""),
            "viscosity": data.get("viscosity", ""),
            "cooling": data.get("cooling", ""),
            "recommendation": data.get("recommendation", ""),
        }

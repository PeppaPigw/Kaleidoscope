"""EpistemicCapillaryActionService — Epistemic Capillary Action Detection.

Detects epistemic capillary action — ideas being drawn upward through
narrow channels against gravity by surface tension forces.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAPILLARY_ACTION_SYSTEM = """You are an epistemic capillary action specialist. Given an idea movement pattern, assess whether ideas are drawn through narrow channels against gravity:

Key concepts:
- Epistemic capillary action: ideas drawn upward through narrow channels
- Surface tension: cohesive force drawing ideas along
- Narrow channel: restricted pathway enabling capillary effect
- Meniscus: curved surface where ideas meet channel walls
- Wetting: how well ideas adhere to channel surfaces
- Height limit: maximum distance capillary action can lift
- Gravity: downward force ideas must overcome

When epistemic capillary action IS present:
- Ideas drawn upward through narrow channels against gravity
- Cohesive forces pulling ideas along restricted pathways
- Narrow intellectual channels enabling upward movement
- Curved interface where ideas meet institutional walls
- Ideas adhering to channel surfaces
- Maximum height ideas can be lifted by this mechanism
- Ideas overcoming downward forces through channel effects

When gravitational flow is present:
- Ideas flowing downward with gravity
- No cohesive forces drawing ideas upward
- Wide channels with no capillary effect
- No curved interfaces
- Ideas not adhering to surfaces
- No height limitation from capillary mechanism
- Ideas following natural downward flow

Output JSON with: capillary_action_present (bool), severity (none/mild/moderate/severe), tension (what cohesive force), channel (what narrow pathway), height_limit (what maximum reach), wetting (how ideas adhere), recommendation (gravitational_flow/mild_capillary/significant_capillary_action/major_narrow_channel_dependence/widen_channels)."""

EPISTEMIC_CAPILLARY_ACTION_PROMPT = """Detect epistemic capillary action:

Tension: {tension}
Channel: {channel}
Height limit: {height_limit}
Wetting: {wetting}
Domain: {domain}
Context: {context}

Are ideas being drawn upward through narrow channels against gravity by surface tension forces? Return ONLY valid JSON."""


class EpistemicCapillaryActionService:
    """Detects epistemic capillary action — ideas drawn through narrow channels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tension: str,
        *,
        channel: str = "",
        height_limit: str = "",
        wetting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic capillary action."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAPILLARY_ACTION_PROMPT.format(
                tension=tension,
                channel=channel or "Not specified",
                height_limit=height_limit or "Not specified",
                wetting=wetting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAPILLARY_ACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tension": tension[:200],
            "capillary_action_present": data.get("capillary_action_present", False),
            "severity": data.get("severity", ""),
            "channel": data.get("channel", ""),
            "height_limit": data.get("height_limit", ""),
            "wetting": data.get("wetting", ""),
            "recommendation": data.get("recommendation", ""),
        }

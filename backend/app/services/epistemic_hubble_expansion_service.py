"""EpistemicHubbleExpansionService — Epistemic Hubble Expansion Detection.

Detects epistemic Hubble expansion — intellectual space itself expanding,
pushing ideas apart proportionally to their distance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HUBBLE_EXPANSION_SYSTEM = """You are an epistemic Hubble expansion specialist. Given an intellectual space, assess whether the space itself is expanding:

Key concepts:
- Epistemic Hubble expansion: intellectual space expanding, pushing ideas apart
- Hubble constant: rate of expansion
- Redshift: ideas stretching as space expands
- Recession velocity: speed ideas move apart
- Cosmological horizon: distance beyond which ideas recede faster than communication
- Accelerating expansion: expansion rate increasing over time
- Comoving distance: distance accounting for expansion

When epistemic Hubble expansion IS present:
- Intellectual space itself expanding between ideas
- Measurable rate of expansion
- Ideas stretching and losing energy as space expands
- Ideas moving apart proportionally to distance
- Horizon beyond which ideas are unreachable
- Expansion rate increasing over time
- Need to account for expansion in measuring distances

When static space is present:
- Intellectual space not expanding
- No expansion rate
- Ideas maintaining their energy
- Ideas not moving apart
- No expansion horizon
- No acceleration
- Simple distance measurement

Output JSON with: hubble_expansion_present (bool), severity (none/mild/moderate/severe), hubble_constant (what expansion rate), redshift (what stretching), cosmological_horizon (what unreachable boundary), acceleration (what rate increase), recommendation (static_space/mild_expansion/significant_hubble_expansion/major_expansion/account_for_expansion)."""

EPISTEMIC_HUBBLE_EXPANSION_PROMPT = """Detect epistemic Hubble expansion:

Hubble constant: {hubble_constant}
Redshift: {redshift}
Cosmological horizon: {cosmological_horizon}
Acceleration: {acceleration}
Domain: {domain}
Context: {context}

Is intellectual space itself expanding, pushing ideas apart proportionally to their distance? Return ONLY valid JSON."""


class EpistemicHubbleExpansionService:
    """Detects epistemic Hubble expansion — intellectual space expanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hubble_constant: str,
        *,
        redshift: str = "",
        cosmological_horizon: str = "",
        acceleration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Hubble expansion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HUBBLE_EXPANSION_PROMPT.format(
                hubble_constant=hubble_constant,
                redshift=redshift or "Not specified",
                cosmological_horizon=cosmological_horizon or "Not specified",
                acceleration=acceleration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HUBBLE_EXPANSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hubble_constant": hubble_constant[:200],
            "hubble_expansion_present": data.get("hubble_expansion_present", False),
            "severity": data.get("severity", ""),
            "redshift": data.get("redshift", ""),
            "cosmological_horizon": data.get("cosmological_horizon", ""),
            "acceleration": data.get("acceleration", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicPNJunctionService — Epistemic P-N Junction Detection.

Detects epistemic P-N junction — the interface between positive and
negative intellectual regions that creates a one-way flow of ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PN_JUNCTION_SYSTEM = """You are an epistemic P-N junction specialist. Given an idea flow pattern, assess whether an interface creates one-way flow:

Key concepts:
- Epistemic P-N junction: interface creating one-way idea flow
- Depletion zone: region emptied of mobile ideas
- Forward bias: condition allowing flow
- Reverse bias: condition blocking flow
- Breakdown: excessive reverse pressure causing flood
- Rectification: converting bidirectional to one-way
- Diffusion: ideas moving from high to low concentration

When epistemic P-N junction IS present:
- Interface between regions creating one-way idea flow
- Region emptied of mobile ideas at the interface
- Conditions that allow flow in one direction
- Conditions that block flow in reverse direction
- Excessive pressure causing breakdown and flooding
- Bidirectional ideas converted to one-way flow
- Ideas moving from high to low concentration

When bidirectional flow is present:
- No interface creating directional preference
- No depleted regions
- Flow possible in both directions equally
- No blocking in either direction
- No breakdown from pressure
- No rectification occurring
- Equilibrium concentration throughout

Output JSON with: pn_junction_present (bool), severity (none/mild/moderate/severe), depletion_zone (what region is emptied), forward_bias (what allows flow), reverse_bias (what blocks flow), breakdown (what causes flooding), recommendation (bidirectional_flow/mild_rectification/significant_pn_junction/major_one_way_flow/remove_junction_barrier)."""

EPISTEMIC_PN_JUNCTION_PROMPT = """Detect epistemic P-N junction:

Depletion zone: {depletion_zone}
Forward bias: {forward_bias}
Reverse bias: {reverse_bias}
Breakdown: {breakdown}
Domain: {domain}
Context: {context}

Is an interface between positive and negative intellectual regions creating a one-way flow of ideas? Return ONLY valid JSON."""


class EpistemicPNJunctionService:
    """Detects epistemic P-N junction — interface creating one-way flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        depletion_zone: str,
        *,
        forward_bias: str = "",
        reverse_bias: str = "",
        breakdown: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic P-N junction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PN_JUNCTION_PROMPT.format(
                depletion_zone=depletion_zone,
                forward_bias=forward_bias or "Not specified",
                reverse_bias=reverse_bias or "Not specified",
                breakdown=breakdown or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PN_JUNCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "depletion_zone": depletion_zone[:200],
            "pn_junction_present": data.get("pn_junction_present", False),
            "severity": data.get("severity", ""),
            "forward_bias": data.get("forward_bias", ""),
            "reverse_bias": data.get("reverse_bias", ""),
            "breakdown": data.get("breakdown", ""),
            "recommendation": data.get("recommendation", ""),
        }

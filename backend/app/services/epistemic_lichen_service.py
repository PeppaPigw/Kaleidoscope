"""EpistemicLichenService — Epistemic Lichen Detection.

Detects epistemic lichen — composite ideas formed from symbiosis
between fundamentally different intellectual organisms.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LICHEN_SYSTEM = """You are an epistemic lichen specialist. Given a composite idea, assess whether fundamentally different intellectual organisms have formed a symbiosis:

Key concepts:
- Epistemic lichen: composite ideas from different intellectual organisms
- Symbiosis: fundamentally different ideas living together as one
- Pioneer species: first ideas to colonize barren intellectual territory
- Slow growth: composite ideas growing very slowly but persistently
- Extreme tolerance: composite ideas surviving where neither component could alone
- Indicator species: composite ideas indicating intellectual environment health
- Mutualism: both components benefiting from the composite

When epistemic lichen IS present:
- Composite ideas formed from fundamentally different intellectual traditions
- Different ideas living together as a unified whole
- Composite ideas pioneering barren intellectual territory
- Very slow but persistent growth of composite ideas
- Composite surviving where neither component could alone
- Composite indicating something about intellectual environment
- Both components benefiting from the combination

When simple ideas are present:
- Ideas from single intellectual tradition
- No composite formation from different traditions
- Ideas not pioneering barren territory
- Normal growth rate of ideas
- Ideas surviving on their own merits
- No indicator function
- No symbiotic combination needed

Output JSON with: lichen_present (bool), severity (none/mild/moderate/severe), components (what different organisms combine), symbiosis (what symbiosis forms), pioneer (what territory is colonized), tolerance (what extreme conditions are survived), recommendation (simple_ideas/mild_composite/significant_lichen/major_symbiotic_organism/nurture_composite_growth)."""

EPISTEMIC_LICHEN_PROMPT = """Detect epistemic lichen:

Components: {components}
Symbiosis: {symbiosis}
Pioneer: {pioneer}
Tolerance: {tolerance}
Domain: {domain}
Context: {context}

Are fundamentally different intellectual organisms forming composite symbiotic ideas? Return ONLY valid JSON."""


class EpistemicLichenService:
    """Detects epistemic lichen — composite ideas from different intellectual organisms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        components: str,
        *,
        symbiosis: str = "",
        pioneer: str = "",
        tolerance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lichen."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LICHEN_PROMPT.format(
                components=components,
                symbiosis=symbiosis or "Not specified",
                pioneer=pioneer or "Not specified",
                tolerance=tolerance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LICHEN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "components": components[:200],
            "lichen_present": data.get("lichen_present", False),
            "severity": data.get("severity", ""),
            "symbiosis": data.get("symbiosis", ""),
            "pioneer": data.get("pioneer", ""),
            "tolerance": data.get("tolerance", ""),
            "recommendation": data.get("recommendation", ""),
        }

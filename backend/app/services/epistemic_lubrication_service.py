"""EpistemicLubricationService — Epistemic Lubrication Detection.

Detects epistemic lubrication — substances reducing friction between
ideas that would otherwise grind against each other destructively.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LUBRICATION_SYSTEM = """You are an epistemic lubrication specialist. Given an idea interaction pattern, assess whether substances reduce friction between ideas:

Key concepts:
- Epistemic lubrication: reducing friction between ideas
- Lubricant: substance that reduces intellectual friction
- Boundary lubrication: thin film preventing direct contact
- Hydrodynamic: thick film completely separating surfaces
- Viscosity: thickness/resistance of the lubricant
- Starvation: insufficient lubricant causing damage
- Contamination: lubricant degraded by foreign material

When epistemic lubrication IS present:
- Substances reducing friction between conflicting ideas
- Specific intellectual lubricant reducing conflict
- Thin protective layer preventing direct clash
- Thick separation completely preventing contact
- Varying thickness of the protective layer
- Insufficient protection causing intellectual damage
- Protective substance degraded by contamination

When direct contact is present:
- Ideas in direct contact without protection
- No lubricant between conflicting ideas
- No protective layer
- No separation between surfaces
- No protective thickness
- No starvation possible
- No contamination concern

Output JSON with: lubrication_present (bool), severity (none/mild/moderate/severe), lubricant (what reduces friction), film_type (boundary or hydrodynamic), starvation (what insufficient protection), contamination (what degrades protection), recommendation (direct_contact/mild_lubrication/significant_lubrication/major_friction_reduction/ensure_adequate_lubrication)."""

EPISTEMIC_LUBRICATION_PROMPT = """Detect epistemic lubrication:

Lubricant: {lubricant}
Film type: {film_type}
Starvation: {starvation}
Contamination: {contamination}
Domain: {domain}
Context: {context}

Are substances reducing friction between ideas that would otherwise grind against each other destructively? Return ONLY valid JSON."""


class EpistemicLubricationService:
    """Detects epistemic lubrication — reducing friction between ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        lubricant: str,
        *,
        film_type: str = "",
        starvation: str = "",
        contamination: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic lubrication."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LUBRICATION_PROMPT.format(
                lubricant=lubricant,
                film_type=film_type or "Not specified",
                starvation=starvation or "Not specified",
                contamination=contamination or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LUBRICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "lubricant": lubricant[:200],
            "lubrication_present": data.get("lubrication_present", False),
            "severity": data.get("severity", ""),
            "film_type": data.get("film_type", ""),
            "starvation": data.get("starvation", ""),
            "contamination": data.get("contamination", ""),
            "recommendation": data.get("recommendation", ""),
        }

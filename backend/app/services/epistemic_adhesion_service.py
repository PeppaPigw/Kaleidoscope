"""EpistemicAdhesionService — Epistemic Adhesion Detection.

Detects epistemic adhesion — ideas sticking together at contact points
through surface forces rather than genuine logical connection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ADHESION_SYSTEM = """You are an epistemic adhesion specialist. Given an idea bonding pattern, assess whether ideas stick through surface forces rather than logic:

Key concepts:
- Epistemic adhesion: ideas sticking through surface forces not logic
- Van der Waals: weak attraction from proximity alone
- Contact area: how much surface is shared
- Surface energy: tendency of surfaces to bond
- Tack: initial stickiness on contact
- Peel strength: force needed to separate
- Cohesive failure: breaking within the bond not at interface

When epistemic adhesion IS present:
- Ideas sticking together through surface forces not logic
- Weak attraction from mere proximity
- Amount of shared surface determining bond strength
- Surfaces naturally tending to bond
- Initial stickiness on first contact
- Significant force needed to separate bonded ideas
- Breaking within the bond rather than at the interface

When logical connection is present:
- Ideas connected through genuine logical links
- Connection from logical necessity not proximity
- Connection strength from argument quality
- No surface tendency to bond
- No initial stickiness
- Easy separation when logic doesn't hold
- Clean separation at logical joints

Output JSON with: adhesion_present (bool), severity (none/mild/moderate/severe), van_der_waals (what proximity attraction), contact_area (what shared surface), peel_strength (what separation force), cohesive_failure (what internal breaking), recommendation (logical_connection/mild_adhesion/significant_adhesion/major_surface_bonding/replace_adhesion_with_logic)."""

EPISTEMIC_ADHESION_PROMPT = """Detect epistemic adhesion:

Van der Waals: {van_der_waals}
Contact area: {contact_area}
Peel strength: {peel_strength}
Cohesive failure: {cohesive_failure}
Domain: {domain}
Context: {context}

Are ideas sticking together at contact points through surface forces rather than genuine logical connection? Return ONLY valid JSON."""


class EpistemicAdhesionService:
    """Detects epistemic adhesion — ideas sticking through surface forces."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        van_der_waals: str,
        *,
        contact_area: str = "",
        peel_strength: str = "",
        cohesive_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic adhesion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ADHESION_PROMPT.format(
                van_der_waals=van_der_waals,
                contact_area=contact_area or "Not specified",
                peel_strength=peel_strength or "Not specified",
                cohesive_failure=cohesive_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ADHESION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "van_der_waals": van_der_waals[:200],
            "adhesion_present": data.get("adhesion_present", False),
            "severity": data.get("severity", ""),
            "contact_area": data.get("contact_area", ""),
            "peel_strength": data.get("peel_strength", ""),
            "cohesive_failure": data.get("cohesive_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }

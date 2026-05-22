"""EpistemicKleinBottleService — Epistemic Klein Bottle Detection.

Detects epistemic Klein bottle — intellectual constructs that cannot be
properly embedded in normal reasoning space without self-intersection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KLEIN_BOTTLE_SYSTEM = """You are an epistemic Klein bottle specialist. Given an intellectual construct, assess whether it cannot be properly embedded without self-intersection:

Key concepts:
- Epistemic Klein bottle: cannot embed without self-intersection
- Self-intersection: argument crossing through itself
- Non-orientability: no consistent inside/outside
- Closed surface: no boundary or edge
- Immersion: representation with self-crossing
- Higher dimension: needing more dimensions to exist properly
- Fundamental group: underlying structure of the surface

When epistemic Klein bottle IS present:
- Constructs that cannot exist without self-contradiction
- Arguments crossing through themselves
- No consistent inside/outside distinction
- No boundary or edge to the argument
- Representation requiring self-crossing
- Needing higher-dimensional thinking to resolve
- Underlying structure creating impossibility

When embeddable construct is present:
- Constructs existing without contradiction
- Arguments not crossing themselves
- Consistent inside/outside distinction
- Clear boundaries and edges
- Clean representation without crossing
- Existing comfortably in normal reasoning
- Simple underlying structure

Output JSON with: klein_bottle_present (bool), severity (none/mild/moderate/severe), self_intersection (what crossing), non_orientability (what lacks distinction), closed_surface (what boundarylessness), higher_dimension (what extra space needed), recommendation (embeddable_construct/mild_klein/significant_klein_bottle/major_self_intersection/move_to_higher_dimension)."""

EPISTEMIC_KLEIN_BOTTLE_PROMPT = """Detect epistemic Klein bottle:

Self-intersection: {self_intersection}
Non-orientability: {non_orientability}
Closed surface: {closed_surface}
Higher dimension: {higher_dimension}
Domain: {domain}
Context: {context}

Is this intellectual construct unable to be properly embedded in normal reasoning space without self-intersection? Return ONLY valid JSON."""


class EpistemicKleinBottleService:
    """Detects epistemic Klein bottle — cannot embed without self-intersection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_intersection: str,
        *,
        non_orientability: str = "",
        closed_surface: str = "",
        higher_dimension: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Klein bottle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KLEIN_BOTTLE_PROMPT.format(
                self_intersection=self_intersection,
                non_orientability=non_orientability or "Not specified",
                closed_surface=closed_surface or "Not specified",
                higher_dimension=higher_dimension or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KLEIN_BOTTLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_intersection": self_intersection[:200],
            "klein_bottle_present": data.get("klein_bottle_present", False),
            "severity": data.get("severity", ""),
            "non_orientability": data.get("non_orientability", ""),
            "closed_surface": data.get("closed_surface", ""),
            "higher_dimension": data.get("higher_dimension", ""),
            "recommendation": data.get("recommendation", ""),
        }

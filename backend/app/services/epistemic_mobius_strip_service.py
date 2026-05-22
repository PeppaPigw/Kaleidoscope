"""EpistemicMobiusStripService — Epistemic Mobius Strip Detection.

Detects epistemic Mobius strip — intellectual arguments that appear to
have two sides but are actually a single continuous surface with no boundary.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOBIUS_STRIP_SYSTEM = """You are an epistemic Mobius strip specialist. Given an intellectual argument, assess whether apparent two-sidedness is actually a single continuous surface:

Key concepts:
- Epistemic Mobius strip: apparent two sides actually one surface
- Non-orientability: no consistent inside/outside distinction
- Half-twist: the transformation creating single-sidedness
- Boundary: edge where the surface ends (absent in Mobius)
- Traversal: following the surface reveals single-sidedness
- Cutting: dividing reveals unexpected topology
- Embedding: how the surface sits in larger space

When epistemic Mobius strip IS present:
- Arguments appearing two-sided but actually continuous
- No consistent distinction between positions
- A twist connecting apparent opposites
- No clear boundary between sides
- Following the argument reveals single surface
- Dividing the argument reveals unexpected connections
- The argument embedded in larger intellectual space

When genuine two-sidedness is present:
- Arguments with genuinely distinct sides
- Consistent distinction between positions
- No twist connecting opposites
- Clear boundaries between sides
- Following each side stays on that side
- Division produces expected separate pieces
- Standard embedding in intellectual space

Output JSON with: mobius_strip_present (bool), severity (none/mild/moderate/severe), non_orientability (what lacks distinction), half_twist (what connects opposites), boundary (what edge is absent), traversal (what reveals unity), recommendation (genuine_two_sides/mild_mobius/significant_mobius_strip/major_single_surface/acknowledge_non_orientability)."""

EPISTEMIC_MOBIUS_STRIP_PROMPT = """Detect epistemic Mobius strip:

Non-orientability: {non_orientability}
Half-twist: {half_twist}
Boundary: {boundary}
Traversal: {traversal}
Domain: {domain}
Context: {context}

Does this intellectual argument appear to have two sides but is actually a single continuous surface with no boundary? Return ONLY valid JSON."""


class EpistemicMobiusStripService:
    """Detects epistemic Mobius strip — apparent two sides actually one surface."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        non_orientability: str,
        *,
        half_twist: str = "",
        boundary: str = "",
        traversal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Mobius strip."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOBIUS_STRIP_PROMPT.format(
                non_orientability=non_orientability,
                half_twist=half_twist or "Not specified",
                boundary=boundary or "Not specified",
                traversal=traversal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOBIUS_STRIP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "non_orientability": non_orientability[:200],
            "mobius_strip_present": data.get("mobius_strip_present", False),
            "severity": data.get("severity", ""),
            "half_twist": data.get("half_twist", ""),
            "boundary": data.get("boundary", ""),
            "traversal": data.get("traversal", ""),
            "recommendation": data.get("recommendation", ""),
        }

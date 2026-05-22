"""EpistemicAbrasionService — Epistemic Abrasion Detection.

Detects epistemic abrasion — ideas wearing down through repeated
contact with harder intellectual surfaces.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABRASION_SYSTEM = """You are an epistemic abrasion specialist. Given an idea wear pattern, assess whether ideas are wearing down through repeated contact:

Key concepts:
- Epistemic abrasion: ideas wearing down through repeated contact
- Hardness: resistance of ideas to being worn
- Grit: roughness of the wearing surface
- Wear rate: how fast ideas are being worn down
- Polish: smoothing from fine abrasion
- Scoring: deep scratches from hard particles
- Debris: worn material accumulating

When epistemic abrasion IS present:
- Ideas wearing down through repeated contact with harder surfaces
- Some ideas more resistant to wear than others
- Roughness of opposing intellectual surfaces
- Rate at which ideas are being diminished
- Ideas being smoothed/simplified by fine wear
- Deep damage from particularly hard encounters
- Worn intellectual material accumulating

When pristine preservation is present:
- Ideas maintaining their form despite contact
- All ideas equally resistant
- Smooth intellectual surfaces
- No wear occurring
- Ideas maintaining complexity
- No deep damage
- No debris from wear

Output JSON with: abrasion_present (bool), severity (none/mild/moderate/severe), hardness (what resists wear), grit (what causes wear), wear_rate (how fast), debris (what accumulates), recommendation (pristine_preservation/mild_wear/significant_abrasion/major_wearing_down/protect_from_contact)."""

EPISTEMIC_ABRASION_PROMPT = """Detect epistemic abrasion:

Hardness: {hardness}
Grit: {grit}
Wear rate: {wear_rate}
Debris: {debris}
Domain: {domain}
Context: {context}

Are ideas wearing down through repeated contact with harder intellectual surfaces? Return ONLY valid JSON."""


class EpistemicAbrasionService:
    """Detects epistemic abrasion — ideas wearing down through contact."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hardness: str,
        *,
        grit: str = "",
        wear_rate: str = "",
        debris: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic abrasion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABRASION_PROMPT.format(
                hardness=hardness,
                grit=grit or "Not specified",
                wear_rate=wear_rate or "Not specified",
                debris=debris or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABRASION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hardness": hardness[:200],
            "abrasion_present": data.get("abrasion_present", False),
            "severity": data.get("severity", ""),
            "grit": data.get("grit", ""),
            "wear_rate": data.get("wear_rate", ""),
            "debris": data.get("debris", ""),
            "recommendation": data.get("recommendation", ""),
        }

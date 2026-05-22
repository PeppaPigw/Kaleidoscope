"""EpistemicMirageService — Epistemic Mirage Detection.

Detects epistemic mirages — illusory knowledge that appears real
from a distance but dissolves upon closer examination.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIRAGE_SYSTEM = """You are an epistemic mirage specialist. Given a knowledge claim, assess whether apparent knowledge dissolves upon closer examination:

Key concepts:
- Epistemic mirage: illusory knowledge appearing real from distance
- Dissolution on examination: knowledge dissolving when examined closely
- Distance illusion: appearing substantive only from far away
- Proximity failure: failing to hold up under close scrutiny
- Surface plausibility: plausible on surface but empty beneath
- Approach disappointment: disappointing when approached closely
- Phantom knowledge: knowledge that isn't actually there

When epistemic mirage IS present:
- Apparent knowledge dissolving upon closer examination
- Knowledge appearing real only from a distance
- Substance disappearing when examined closely
- Failing to hold up under close scrutiny
- Plausible on surface but empty beneath
- Disappointing when approached for actual use
- Knowledge that isn't actually there when needed

When genuine knowledge is present:
- Knowledge holding up under close examination
- Substance present at all distances
- Surviving close scrutiny
- Holding up under detailed examination
- Substantive beneath the surface
- Delivering when approached for use
- Actually present when needed

Output JSON with: mirage_present (bool), severity (none/mild/moderate/severe), claim (what knowledge is claimed), appearance (what it appears to be), dissolution (how it dissolves), distance (from what distance it appears real), recommendation (genuine_knowledge/mild_overstatement/significant_mirage/major_phantom_knowledge/verify_before_relying)."""

EPISTEMIC_MIRAGE_PROMPT = """Detect epistemic mirage:

Claim: {claim}
Appearance: {appearance}
Dissolution: {dissolution}
Distance: {distance}
Domain: {domain}
Context: {context}

Does apparent knowledge dissolve upon closer examination? Return ONLY valid JSON."""


class EpistemicMirageService:
    """Detects epistemic mirages — illusory knowledge dissolving on examination."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        appearance: str = "",
        dissolution: str = "",
        distance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mirage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIRAGE_PROMPT.format(
                claim=claim,
                appearance=appearance or "Not specified",
                dissolution=dissolution or "Not specified",
                distance=distance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIRAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "mirage_present": data.get("mirage_present", False),
            "severity": data.get("severity", ""),
            "appearance": data.get("appearance", ""),
            "dissolution": data.get("dissolution", ""),
            "distance": data.get("distance", ""),
            "recommendation": data.get("recommendation", ""),
        }

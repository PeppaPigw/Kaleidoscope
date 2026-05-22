"""EpistemicFairyRingService — Epistemic Fairy Ring Detection.

Detects epistemic fairy rings — ideas growing outward in expanding
circles, leaving dead centers where original insights once stood.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FAIRY_RING_SYSTEM = """You are an epistemic fairy ring specialist. Given an idea growth pattern, assess whether ideas are expanding outward leaving dead centers:

Key concepts:
- Epistemic fairy ring: ideas growing outward in expanding circles
- Dead center: original insight area now barren
- Expanding frontier: active growth only at the edges
- Nutrient depletion: original territory exhausted of intellectual nutrients
- Ring expansion: ideas moving further from original insight
- Apparent mystery: pattern appearing mysterious without understanding growth
- Annual growth: measurable rate of outward expansion

When epistemic fairy ring IS present:
- Ideas growing outward in expanding circles
- Original insight area now barren and exhausted
- Active intellectual growth only at the edges
- Original territory depleted of intellectual nutrients
- Ideas moving progressively further from original insight
- Pattern appearing mysterious to those who don't understand it
- Measurable rate of outward expansion from center

When centered growth is present:
- Ideas growing from and maintaining their center
- Original insight area remaining vital
- Growth occurring throughout, not just at edges
- Original territory still rich with nutrients
- Ideas remaining connected to original insight
- Growth pattern clear and understandable
- No outward expansion leaving dead centers

Output JSON with: fairy_ring_present (bool), severity (none/mild/moderate/severe), ideas (what ideas form the ring), dead_center (what original insight is lost), frontier (what active edge grows), depletion (what nutrients are exhausted), recommendation (centered_growth/mild_expansion/significant_ring/major_dead_center/reconnect_to_original_insight)."""

EPISTEMIC_FAIRY_RING_PROMPT = """Detect epistemic fairy ring:

Ideas: {ideas}
Dead center: {dead_center}
Frontier: {frontier}
Depletion: {depletion}
Domain: {domain}
Context: {context}

Are ideas growing outward in expanding circles leaving dead centers where original insights stood? Return ONLY valid JSON."""


class EpistemicFairyRingService:
    """Detects epistemic fairy rings — outward expansion leaving dead centers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        dead_center: str = "",
        frontier: str = "",
        depletion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fairy ring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FAIRY_RING_PROMPT.format(
                ideas=ideas,
                dead_center=dead_center or "Not specified",
                frontier=frontier or "Not specified",
                depletion=depletion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FAIRY_RING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "fairy_ring_present": data.get("fairy_ring_present", False),
            "severity": data.get("severity", ""),
            "dead_center": data.get("dead_center", ""),
            "frontier": data.get("frontier", ""),
            "depletion": data.get("depletion", ""),
            "recommendation": data.get("recommendation", ""),
        }

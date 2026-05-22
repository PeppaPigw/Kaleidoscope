"""EpistemicFloodService — Epistemic Flood Detection.

Detects epistemic floods — overwhelming volumes of information
that destroy existing knowledge structures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FLOOD_SYSTEM = """You are an epistemic flood specialist. Given an information volume pattern, assess whether overwhelming volumes destroy knowledge structures:

Key concepts:
- Epistemic flood: overwhelming information destroying structures
- Volume overwhelm: volume exceeding processing capacity
- Structure destruction: existing structures destroyed by volume
- Sorting failure: inability to sort signal from noise
- Infrastructure damage: knowledge infrastructure damaged
- Recovery difficulty: difficulty recovering after flood
- Sediment deposit: random information deposited everywhere

When epistemic flood IS present:
- Overwhelming volumes of information
- Volume exceeding all processing capacity
- Existing knowledge structures destroyed
- Inability to sort signal from noise in volume
- Knowledge infrastructure damaged by volume
- Difficult to recover after the flood
- Random information deposited everywhere

When manageable volume is present:
- Information volume within processing capacity
- Volume manageable with existing resources
- Knowledge structures intact and functioning
- Signal distinguishable from noise
- Knowledge infrastructure functioning
- Normal processing and integration
- Information appropriately organized

Output JSON with: flood_present (bool), severity (none/mild/moderate/severe), source (what source floods), volume (how much volume), destruction (what structures destroyed), recovery (recovery difficulty), recommendation (manageable_volume/mild_overflow/significant_flood/major_structural_destruction/build_flood_defenses)."""

EPISTEMIC_FLOOD_PROMPT = """Detect epistemic flood:

Source: {source}
Volume: {volume}
Destruction: {destruction}
Recovery: {recovery}
Domain: {domain}
Context: {context}

Are overwhelming volumes of information destroying knowledge structures? Return ONLY valid JSON."""


class EpistemicFloodService:
    """Detects epistemic floods — overwhelming information destroying structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source: str,
        *,
        volume: str = "",
        destruction: str = "",
        recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic flood."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FLOOD_PROMPT.format(
                source=source,
                volume=volume or "Not specified",
                destruction=destruction or "Not specified",
                recovery=recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FLOOD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source": source[:200],
            "flood_present": data.get("flood_present", False),
            "severity": data.get("severity", ""),
            "volume": data.get("volume", ""),
            "destruction": data.get("destruction", ""),
            "recovery": data.get("recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }

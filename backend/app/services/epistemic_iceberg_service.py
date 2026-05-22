"""EpistemicIcebergService — Epistemic Iceberg Detection.

Detects epistemic icebergs — ideas where the visible portion is
a tiny fraction of the hidden mass beneath the surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ICEBERG_SYSTEM = """You are an epistemic iceberg specialist. Given an idea, assess whether the visible portion is a tiny fraction of hidden mass:

Key concepts:
- Epistemic iceberg: visible idea is tiny fraction of hidden mass
- Submerged mass: vast hidden complexity beneath surface
- Waterline: boundary between visible and hidden portions
- Tip: the small visible portion that people engage with
- Draft: how deep the hidden portion extends
- Calving: pieces breaking off from hidden mass
- Collision risk: danger from engaging only with visible portion

When epistemic iceberg IS present:
- Visible portion of idea is tiny fraction of total
- Vast hidden complexity beneath the surface
- Clear boundary between what's visible and what's hidden
- People engaging only with the small visible tip
- Hidden portion extending much deeper than expected
- Pieces of hidden complexity occasionally surfacing
- Danger from engaging only with visible portion

When fully visible ideas are present:
- Entire idea visible and accessible
- No hidden complexity beneath surface
- No boundary between visible and hidden
- People engaging with the full idea
- No unexpected depth
- No hidden pieces surfacing unexpectedly
- Safe to engage with what's visible

Output JSON with: iceberg_present (bool), severity (none/mild/moderate/severe), tip (what visible portion shows), submerged (what hidden mass exists), draft (how deep it extends), collision_risk (what danger from surface engagement), recommendation (fully_visible/mild_depth/significant_iceberg/major_hidden_mass/explore_beneath_surface)."""

EPISTEMIC_ICEBERG_PROMPT = """Detect epistemic iceberg:

Tip: {tip}
Submerged: {submerged}
Draft: {draft}
Collision risk: {collision_risk}
Domain: {domain}
Context: {context}

Is the visible portion of this idea a tiny fraction of vast hidden mass beneath the surface? Return ONLY valid JSON."""


class EpistemicIcebergService:
    """Detects epistemic icebergs — visible ideas hiding vast submerged complexity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tip: str,
        *,
        submerged: str = "",
        draft: str = "",
        collision_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic iceberg."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ICEBERG_PROMPT.format(
                tip=tip,
                submerged=submerged or "Not specified",
                draft=draft or "Not specified",
                collision_risk=collision_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ICEBERG_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tip": tip[:200],
            "iceberg_present": data.get("iceberg_present", False),
            "severity": data.get("severity", ""),
            "submerged": data.get("submerged", ""),
            "draft": data.get("draft", ""),
            "collision_risk": data.get("collision_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }

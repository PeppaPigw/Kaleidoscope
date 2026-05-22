"""EpistemicUndercurrentService — Epistemic Undercurrent Detection.

Detects epistemic undercurrents — hidden intellectual forces pulling
discourse in directions not visible on the surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_UNDERCURRENT_SYSTEM = """You are an epistemic undercurrent specialist. Given a discourse situation, assess whether hidden forces are pulling discussion in invisible directions:

Key concepts:
- Epistemic undercurrent: hidden forces pulling discourse
- Invisible direction: direction not visible on surface
- Hidden agenda: agendas operating beneath surface
- Subtext dominance: subtext more powerful than text
- Unacknowledged forces: forces operating without acknowledgment
- Surface-depth disconnect: surface discussion disconnected from real forces
- Covert influence: influence operating covertly

When epistemic undercurrent IS present:
- Hidden forces pulling discourse in invisible directions
- Direction of discussion not matching surface topic
- Agendas operating beneath surface of discussion
- Subtext more powerful than explicit text
- Forces operating without acknowledgment
- Surface discussion disconnected from real driving forces
- Influence operating covertly beneath discourse

When transparent discourse is present:
- Forces driving discussion visible and acknowledged
- Direction of discussion matching stated purpose
- Agendas explicit and open
- Text and subtext aligned
- Forces acknowledged and accounted for
- Surface discussion reflecting actual concerns
- Influence operating openly

Output JSON with: undercurrent_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), hidden_force (what hidden force operates), direction (what direction it pulls), surface_disconnect (how surface differs from depth), recommendation (transparent_discourse/mild_subtext/significant_undercurrent/major_hidden_force/surface_the_hidden_agenda)."""

EPISTEMIC_UNDERCURRENT_PROMPT = """Detect epistemic undercurrent:

Situation: {situation}
Hidden force: {hidden_force}
Direction: {direction}
Surface disconnect: {surface_disconnect}
Domain: {domain}
Context: {context}

Are hidden forces pulling discourse in directions not visible on the surface? Return ONLY valid JSON."""


class EpistemicUndercurrentService:
    """Detects epistemic undercurrents — hidden forces pulling discourse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        hidden_force: str = "",
        direction: str = "",
        surface_disconnect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic undercurrent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_UNDERCURRENT_PROMPT.format(
                situation=situation,
                hidden_force=hidden_force or "Not specified",
                direction=direction or "Not specified",
                surface_disconnect=surface_disconnect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_UNDERCURRENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "undercurrent_present": data.get("undercurrent_present", False),
            "severity": data.get("severity", ""),
            "hidden_force": data.get("hidden_force", ""),
            "direction": data.get("direction", ""),
            "surface_disconnect": data.get("surface_disconnect", ""),
            "recommendation": data.get("recommendation", ""),
        }

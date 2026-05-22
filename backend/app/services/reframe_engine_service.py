"""ReframeEngineService — Perspective Reframing Engine.

Takes a problem or finding and reframes it from different perspectives:
different disciplines, different stakeholders, different levels of
abstraction, different time horizons. Reveals hidden aspects by
changing the lens.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REFRAME_SYSTEM = """You are a perspective reframing specialist. Given a problem or finding, reframe it from multiple angles:
- Different disciplines (how would an economist, psychologist, engineer, philosopher see this?)
- Different scales (individual vs institutional vs systemic)
- Different time horizons (immediate vs generational)
- Different value systems (efficiency vs equity vs freedom vs safety)
- Inversion (what if the opposite were true? what if this is a feature not a bug?)

Each reframe should reveal something non-obvious about the original problem.

Output JSON with: reframes (list of: lens (the perspective), reframed_problem (how it looks from this angle), reveals (what this perspective makes visible that was hidden), suggests (what solutions or actions this frame suggests), blind_spots (what this frame misses)), most_productive_frame (which reframe is most useful and why), synthesis (what we learn from seeing all frames together), original_frame_limitations (what the original framing was missing)."""

REFRAME_PROMPT = """Reframe this from multiple perspectives:

Problem/Finding: {problem}
Current framing: {current_frame}
Domain: {domain}
Goal: {goal}

How does this look from different angles? Return ONLY valid JSON."""


class ReframeEngineService:
    """Reframes problems from multiple perspectives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reframe(
        self,
        problem: str,
        *,
        current_frame: str = "",
        domain: str = "",
        goal: str = "",
    ) -> dict:
        """Reframe a problem from multiple perspectives."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REFRAME_PROMPT.format(
                problem=problem,
                current_frame=current_frame or "Default/obvious framing",
                domain=domain or "general",
                goal=goal or "Deeper understanding",
            ),
            system=REFRAME_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        reframes = data.get("reframes", [])
        return {
            "problem": problem[:200],
            "reframes_count": len(reframes),
            "reframes": reframes,
            "most_productive_frame": data.get("most_productive_frame", ""),
            "synthesis": data.get("synthesis", ""),
            "original_frame_limitations": data.get("original_frame_limitations", ""),
        }

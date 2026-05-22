"""OvertonWindowService — Idea Acceptability & Window Mapping.

Maps where an idea sits on the spectrum of acceptability (unthinkable
to policy) and how that window has shifted over time. Identifies
whether an idea is ahead of its time, mainstream, or losing ground.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERTON_SYSTEM = """You are an Overton window analyst. Given an idea or position, map where it sits on the acceptability spectrum:
- Unthinkable → Radical → Acceptable → Sensible → Popular → Policy
- Where was this idea 10 years ago? Where is it now? Where is it heading?
- What moved the window (events, advocates, evidence, cultural shifts)?
- Is the idea ahead of its time, mainstream, or losing ground?
- What would need to happen for it to become more/less acceptable?

Output JSON with: current_position (unthinkable/radical/acceptable/sensible/popular/policy), position_10_years_ago (same scale), trajectory (advancing/stable/retreating), window_movers (list of: event_or_factor, direction (opened/closed), magnitude (minor/moderate/major)), expert_vs_public (where experts place it vs where public places it), controversy_level (0-1), taboo_factors (what makes it hard to discuss), mainstreaming_path (what would move it toward policy), marginalization_path (what would push it back toward unthinkable), analogous_ideas (ideas that followed similar trajectories), tipping_point (what event/evidence would rapidly shift acceptability), current_advocates (who champions this), current_opponents (who opposes this), recommendation (ahead_of_time/well_timed/behind_the_curve/permanently_fringe)."""

OVERTON_PROMPT = """Map the Overton window:

Idea/Position: {idea}
Field/Domain: {domain}
Audience: {audience}
Context: {context}

Where does this sit on the acceptability spectrum? Return ONLY valid JSON."""


class OvertonWindowService:
    """Maps idea acceptability and Overton window position."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_position(
        self,
        idea: str,
        *,
        domain: str = "",
        audience: str = "",
        context: str = "",
    ) -> dict:
        """Map Overton window position."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERTON_PROMPT.format(
                idea=idea,
                domain=domain or "general",
                audience=audience or "General public",
                context=context or "No additional context",
            ),
            system=OVERTON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "current_position": data.get("current_position", ""),
            "position_10_years_ago": data.get("position_10_years_ago", ""),
            "trajectory": data.get("trajectory", ""),
            "window_movers": data.get("window_movers", []),
            "expert_vs_public": data.get("expert_vs_public", ""),
            "controversy_level": data.get("controversy_level", 0),
            "taboo_factors": data.get("taboo_factors", ""),
            "mainstreaming_path": data.get("mainstreaming_path", ""),
            "marginalization_path": data.get("marginalization_path", ""),
            "analogous_ideas": data.get("analogous_ideas", []),
            "tipping_point": data.get("tipping_point", ""),
            "current_advocates": data.get("current_advocates", ""),
            "current_opponents": data.get("current_opponents", ""),
            "recommendation": data.get("recommendation", ""),
        }

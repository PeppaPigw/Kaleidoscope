"""ResearchPriorityRankerService — Strategic Research Prioritization.

Given limited resources, ranks research questions or directions by
expected value: combining probability of success, impact if successful,
resource cost, time sensitivity, and strategic positioning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRIORITIZE_SYSTEM = """You are a research strategy advisor. Given multiple research directions and resource constraints, rank them by expected value. Consider:
- Probability of success (feasibility)
- Impact if successful (importance)
- Resource cost (time, money, people)
- Time sensitivity (will the window close?)
- Strategic positioning (does this enable future work?)
- Information value (will we learn something regardless of outcome?)

Output JSON with: priorities (list of direction/rank/expected_value 0-1/feasibility 0-1/impact 0-1/cost low|medium|high/time_sensitivity urgent|high|medium|low/strategic_value 0-1/rationale), meta.top_recommendation, meta.avoid (what NOT to pursue and why), meta.portfolio_advice (how to balance the portfolio), meta.resource_allocation (suggested % allocation across top items)."""

PRIORITIZE_PROMPT = """Prioritize these research directions:

Directions:
{directions_text}

Constraints: {constraints}
Resources: {resources}
Domain: {domain}
Goal: {goal}

Rank by expected value. Return ONLY valid JSON."""


class ResearchPriorityRankerService:
    """Ranks research directions by expected value."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def prioritize(
        self,
        directions: list[str],
        *,
        constraints: str = "",
        resources: str = "",
        domain: str = "",
        goal: str = "",
    ) -> dict:
        """Rank research directions by expected value."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        directions_text = "\n".join(f"{i+1}. {d}" for i, d in enumerate(directions[:10]))

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRIORITIZE_PROMPT.format(
                directions_text=directions_text,
                constraints=constraints or "Standard academic constraints",
                resources=resources or "Limited team, moderate compute",
                domain=domain or "research",
                goal=goal or "Maximize research impact",
            ),
            system=PRIORITIZE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        meta = data.get("meta", {})

        return {
            "priorities": data.get("priorities", []),
            "top_recommendation": meta.get("top_recommendation", ""),
            "avoid": meta.get("avoid", ""),
            "portfolio_advice": meta.get("portfolio_advice", ""),
            "resource_allocation": meta.get("resource_allocation", {}),
        }

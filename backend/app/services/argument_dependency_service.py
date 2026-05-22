"""ArgumentDependencyService — Premise-Conclusion Dependency Mapping.

Takes an argument and maps which conclusions depend on which premises.
Shows what falls if any single premise is removed, identifies load-bearing
vs decorative premises, and finds single points of failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEPENDENCY_SYSTEM = """You are an argument dependency analyst. Given an argument, map the dependency structure:
- Which conclusions depend on which premises?
- What's load-bearing (remove it and the argument collapses)?
- What's decorative (remove it and nothing changes)?
- Are there single points of failure?
- What's the minimum set of premises needed for the conclusion?
- Are there hidden premises (unstated assumptions the argument requires)?

Output JSON with: premises (list of: id, statement, load_bearing (bool), confidence (0-1)), conclusions (list of: id, statement, depends_on (list of premise ids)), hidden_premises (list of unstated assumptions), single_points_of_failure (premise ids that alone would collapse the argument), minimum_sufficient_set (smallest set of premises that supports the conclusion), redundancy_score (0-1, how much redundancy/backup the argument has), weakest_link (the premise most likely to be false), if_weakest_fails (what survives)."""

DEPENDENCY_PROMPT = """Map argument dependencies:

Argument: {argument}
Main conclusion: {conclusion}
Domain: {domain}

What depends on what? Return ONLY valid JSON."""


class ArgumentDependencyService:
    """Maps premise-conclusion dependencies in arguments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_dependencies(
        self,
        argument: str,
        *,
        conclusion: str = "",
        domain: str = "",
    ) -> dict:
        """Map argument dependencies."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEPENDENCY_PROMPT.format(
                argument=argument,
                conclusion=conclusion or "Not explicitly stated",
                domain=domain or "general",
            ),
            system=DEPENDENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        premises = data.get("premises", [])
        return {
            "premises_count": len(premises),
            "premises": premises,
            "conclusions": data.get("conclusions", []),
            "hidden_premises": data.get("hidden_premises", []),
            "single_points_of_failure": data.get("single_points_of_failure", []),
            "minimum_sufficient_set": data.get("minimum_sufficient_set", []),
            "redundancy_score": data.get("redundancy_score", 0),
            "weakest_link": data.get("weakest_link", ""),
            "if_weakest_fails": data.get("if_weakest_fails", ""),
        }

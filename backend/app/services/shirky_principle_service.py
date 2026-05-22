"""ShirkyPrincipleService — Shirky Principle Detection.

Detects Shirky principle — institutions will try to preserve the
problem to which they are the solution. Clay Shirky. Organizations
that exist to solve a problem have a perverse incentive to ensure
the problem persists, because solving it would eliminate their
reason for existing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SHIRKY_PRINCIPLE_SYSTEM = """You are a Shirky principle specialist. Given an institutional behavior, assess whether an organization is preserving the problem it was created to solve:

Key concepts (Shirky):
- Shirky principle: institutions preserve the problem they solve
- Self-preservation instinct: organizations resist their own obsolescence
- Perverse incentive: solving the problem eliminates the organization
- Mission drift: shifting from solving to managing the problem
- Institutional capture: the institution becomes the point, not the mission
- Solution resistance: actively or passively preventing resolution
- Bureaucratic immortality: organizations that outlive their purpose

When Shirky principle IS present:
- An organization resists solutions that would make it unnecessary
- Resources are spent on managing rather than solving the problem
- Success metrics measure activity rather than problem reduction
- The organization grows even as the problem persists or worsens
- Solutions that would eliminate the need for the organization are dismissed
- The organization redefines the problem to ensure perpetual relevance
- Staff incentives align with problem persistence, not resolution

When institutional persistence IS appropriate:
- The problem is genuinely ongoing and requires permanent attention
- The organization is adapting to new manifestations of the problem
- Institutional knowledge is valuable for related future problems
- The organization is transitioning to new missions as old ones resolve
- Maintenance requires ongoing effort even after initial solution
- The organization acknowledges and measures problem reduction
- Sunset clauses or success criteria exist

Output JSON with: shirky_principle_present (bool), severity (none/mild/moderate/severe), institution (what organization is analyzed), problem (what problem it was created to solve), preservation_behavior (how is the problem being preserved), incentive_structure (what incentives exist), solution_resistance (what solutions are being resisted), recommendation (persistence_appropriate/mild_self_preservation/significant_shirky/major_problem_preservation/align_incentives_with_resolution)."""

SHIRKY_PRINCIPLE_PROMPT = """Detect Shirky principle:

Institution: {institution}
Problem: {problem}
Behavior: {behavior}
Solutions resisted: {solutions}
Domain: {domain}
Context: {context}

Is this institution preserving the problem it was created to solve? Return ONLY valid JSON."""


class ShirkyPrincipleService:
    """Detects Shirky principle — institutions preserving their problem."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        institution: str,
        *,
        problem: str = "",
        behavior: str = "",
        solutions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Shirky principle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SHIRKY_PRINCIPLE_PROMPT.format(
                institution=institution,
                problem=problem or "Not specified",
                behavior=behavior or "Not specified",
                solutions=solutions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SHIRKY_PRINCIPLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "institution": institution[:200],
            "shirky_principle_present": data.get("shirky_principle_present", False),
            "severity": data.get("severity", ""),
            "preservation_behavior": data.get("preservation_behavior", ""),
            "incentive_structure": data.get("incentive_structure", ""),
            "solution_resistance": data.get("solution_resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }

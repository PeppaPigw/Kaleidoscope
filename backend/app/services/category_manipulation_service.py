"""CategoryManipulationService — Category Manipulation Detection.

Detects category manipulation — manipulating categorical boundaries
to include or exclude items for rhetorical effect, where the
definition of a category is adjusted to serve an argument.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CATEGORY_MANIPULATION_SYSTEM = """You are a category manipulation specialist. Given an argument, assess whether categories are being manipulated for rhetorical effect:

Key concepts:
- Category manipulation: adjusting boundaries for rhetorical effect
- Gerrymandering categories: drawing lines to serve conclusions
- Strategic inclusion: including items to inflate a category
- Strategic exclusion: excluding items to deflate a category
- Definition shifting: changing definitions mid-argument
- No true Scotsman variant: excluding counterexamples by redefinition
- Category stretching: expanding categories beyond valid use

When category manipulation IS present:
- Category boundaries adjusted to serve argument
- Items strategically included or excluded
- Definitions shifted to support conclusions
- Counterexamples excluded by redefinition
- Categories stretched beyond valid application
- Boundaries drawn to produce desired result
- Same items categorized differently for different arguments

When category refinement is appropriate:
- Boundaries refined based on evidence
- Definitions clarified for precision
- Categories updated as understanding grows
- Inclusion/exclusion criteria explicit and principled
- Same criteria applied consistently
- Refinement improves rather than serves argument
- Category boundaries justified independently

Output JSON with: manipulation_present (bool), severity (none/mild/moderate/severe), argument (what argument is made), category (what category is manipulated), manipulation (how boundaries are adjusted), effect (what rhetorical effect is achieved), recommendation (appropriate_category_refinement/mild_boundary_flexibility/significant_category_manipulation/major_rhetorical_gerrymandering/apply_consistent_criteria)."""

CATEGORY_MANIPULATION_PROMPT = """Detect category manipulation:

Argument: {argument}
Category used: {category}
Inclusion criteria: {inclusion}
Exclusion criteria: {exclusion}
Domain: {domain}
Context: {context}

Are category boundaries being manipulated for rhetorical effect? Return ONLY valid JSON."""


class CategoryManipulationService:
    """Detects category manipulation — adjusting boundaries for rhetorical effect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        category: str = "",
        inclusion: str = "",
        exclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect category manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CATEGORY_MANIPULATION_PROMPT.format(
                argument=argument,
                category=category or "Not specified",
                inclusion=inclusion or "Not specified",
                exclusion=exclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CATEGORY_MANIPULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "manipulation_present": data.get("manipulation_present", False),
            "severity": data.get("severity", ""),
            "category": data.get("category", ""),
            "manipulation": data.get("manipulation", ""),
            "effect": data.get("effect", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicCategoryHierarchyService — Epistemic Category Hierarchy Detection.

Detects epistemic category hierarchy imposition — imposing false hierarchies
on non-hierarchical categories, creating unwarranted rankings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATEGORY_HIERARCHY_SYSTEM = """You are an epistemic category hierarchy specialist. Given false hierarchies imposed on categories, assess category hierarchy imposition:

Key concepts:
- Epistemic category hierarchy: imposing false hierarchies on non-hierarchical categories
- Unwarranted ranking: ranking categories that aren't naturally ranked
- Value hierarchy imposition: imposing value hierarchies on descriptive categories
- Linear ordering: forcing linear order on multidimensional categories
- Primitive-advanced framing: framing categories as primitive vs advanced
- Natural hierarchy assumption: assuming hierarchies are natural not constructed
- Ranking as classification: confusing ranking with classification

When epistemic category hierarchy IS present:
- False hierarchies imposed
- Unwarranted rankings created
- Value hierarchies on descriptive categories
- Linear order forced
- Primitive-advanced framing used
- Natural hierarchy assumed
- Ranking confused with classification

When no category hierarchy imposition:
- Hierarchies justified
- Rankings warranted
- Value and description distinguished
- Multidimensionality preserved
- Framing neutral
- Hierarchy construction acknowledged
- Classification and ranking distinguished

Output JSON with: category_hierarchy_detected (bool), severity (none/mild/moderate/severe), unwarranted_ranking (what unwarranted rankings), value_hierarchy (what value hierarchies imposed), linear_ordering (what linear order forced), primitive_advanced (what primitive-advanced framing), recommendation (no_category_hierarchy/mild_hierarchy_awareness/significant_ranking_questioning/major_intensive_hierarchy_dissolution/emergency_complete_category_hierarchy)."""

EPISTEMIC_CATEGORY_HIERARCHY_PROMPT = """Detect epistemic category hierarchy imposition:

Unwarranted ranking: {unwarranted_ranking}
Value hierarchy: {value_hierarchy}
Linear ordering: {linear_ordering}
Primitive-advanced framing: {primitive_advanced}
Domain: {domain}
Context: {context}

Are false hierarchies being imposed on non-hierarchical categories? Return ONLY valid JSON."""


class EpistemicCategoryHierarchyService:
    """Detects epistemic category hierarchy — false rankings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unwarranted_ranking: str,
        *,
        value_hierarchy: str = "",
        linear_ordering: str = "",
        primitive_advanced: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category hierarchy imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATEGORY_HIERARCHY_PROMPT.format(
                unwarranted_ranking=unwarranted_ranking,
                value_hierarchy=value_hierarchy or "Not specified",
                linear_ordering=linear_ordering or "Not specified",
                primitive_advanced=primitive_advanced or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATEGORY_HIERARCHY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unwarranted_ranking": unwarranted_ranking[:200],
            "category_hierarchy_detected": data.get("category_hierarchy_detected", False),
            "severity": data.get("severity", ""),
            "value_hierarchy": data.get("value_hierarchy", ""),
            "linear_ordering": data.get("linear_ordering", ""),
            "primitive_advanced": data.get("primitive_advanced", ""),
            "recommendation": data.get("recommendation", ""),
        }

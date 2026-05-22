"""CategoryErrorService — Category Error Detection.

Detects category errors — applying concepts from one category to
another where they don't belong, confusing different logical types
or levels of description.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CATEGORY_ERROR_SYSTEM = """You are a category error specialist. Given a claim or argument, assess whether concepts are being applied across incompatible categories:

Key concepts:
- Category error: applying concept to wrong logical type
- Type confusion: confusing different levels of description
- Ryle's ghost in the machine: treating mental as physical category
- Level confusion: mixing levels of analysis inappropriately
- Reification: treating abstract as concrete
- Anthropomorphism: applying human categories to non-human
- Mechanomorphism: applying mechanical categories to human

When a category error IS present:
- Concept applied to logically incompatible category
- Different levels of description confused
- Abstract treated as concrete or vice versa
- Properties of one type attributed to another type
- Question makes no sense given the category of the subject
- Logical grammar violated
- Type boundaries crossed without justification

When cross-category application is appropriate:
- Metaphor explicitly acknowledged
- Analogy used for illumination with limits stated
- Genuine structural similarity justifies transfer
- Category boundaries genuinely unclear
- Novel theoretical framework redefines categories
- Cross-level explanation with appropriate caveats
- Productive category-crossing in creative thought

Output JSON with: error_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), category_a (source category), category_b (target category), confusion (what is confused), recommendation (appropriate_application/mild_type_confusion/significant_category_error/major_logical_type_violation/respect_categories)."""

CATEGORY_ERROR_PROMPT = """Detect category error:

Claim: {claim}
Subject: {subject}
Predicate: {predicate}
Categories involved: {categories}
Domain: {domain}
Context: {context}

Are concepts being applied across incompatible logical categories? Return ONLY valid JSON."""


class CategoryErrorService:
    """Detects category errors — applying concepts across incompatible categories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        subject: str = "",
        predicate: str = "",
        categories: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect category error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CATEGORY_ERROR_PROMPT.format(
                claim=claim,
                subject=subject or "Not specified",
                predicate=predicate or "Not specified",
                categories=categories or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CATEGORY_ERROR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "error_present": data.get("error_present", False),
            "severity": data.get("severity", ""),
            "category_a": data.get("category_a", ""),
            "category_b": data.get("category_b", ""),
            "confusion": data.get("confusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

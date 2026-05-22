"""EpistemicFramingCategoryService — Epistemic Category Framing Detection.

Detects epistemic framing category manipulation — framing category membership
to change how something is evaluated or perceived.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAMING_CATEGORY_SYSTEM = """You are an epistemic framing category specialist. Given category framing, assess classification manipulation:

Key concepts:
- Epistemic category framing: framing category membership to change evaluation
- Strategic classification: classifying things into categories that favor conclusion
- Category boundary manipulation: moving category boundaries to include/exclude
- Prototype framing: comparing to category prototypes to bias judgment
- Euphemistic categorization: using euphemistic categories to soften perception
- Dysphemistic categorization: using harsh categories to worsen perception
- Category level manipulation: choosing abstraction level to change evaluation

When epistemic category framing IS present:
- Category membership framed strategically
- Classification biased
- Category boundaries manipulated
- Prototypes used to bias
- Euphemistic categories used
- Dysphemistic categories used
- Abstraction level manipulated

When no category framing:
- Categories natural and justified
- Classification appropriate
- Boundaries clear and fair
- Prototypes not exploited
- Categories neutral
- Abstraction level appropriate
- Multiple categorizations considered

Output JSON with: category_framing_detected (bool), severity (none/mild/moderate/severe), strategic_classification (what strategically classified), boundary_manipulation (what boundaries manipulated), euphemistic_categorization (what euphemistically categorized), abstraction_level_manipulation (what abstraction manipulated), recommendation (no_category_framing/mild_category_justification/significant_reclassification/major_intensive_category_audit/emergency_complete_category_manipulation)."""

EPISTEMIC_FRAMING_CATEGORY_PROMPT = """Detect epistemic category framing manipulation:

Strategic classification: {strategic_classification}
Boundary manipulation: {boundary_manipulation}
Euphemistic categorization: {euphemistic_categorization}
Abstraction level manipulation: {abstraction_level_manipulation}
Domain: {domain}
Context: {context}

Is category membership being framed to change evaluation? Return ONLY valid JSON."""


class EpistemicFramingCategoryService:
    """Detects epistemic category framing — classification manipulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategic_classification: str,
        *,
        boundary_manipulation: str = "",
        euphemistic_categorization: str = "",
        abstraction_level_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category framing manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAMING_CATEGORY_PROMPT.format(
                strategic_classification=strategic_classification,
                boundary_manipulation=boundary_manipulation or "Not specified",
                euphemistic_categorization=euphemistic_categorization or "Not specified",
                abstraction_level_manipulation=abstraction_level_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAMING_CATEGORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategic_classification": strategic_classification[:200],
            "category_framing_detected": data.get("category_framing_detected", False),
            "severity": data.get("severity", ""),
            "boundary_manipulation": data.get("boundary_manipulation", ""),
            "euphemistic_categorization": data.get("euphemistic_categorization", ""),
            "abstraction_level_manipulation": data.get("abstraction_level_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicLanguageCategoryManipulationService - Epistemic Language Category Manipulation Detection.

Detects epistemic language category manipulation - strategic
classification that changes conclusions by moving category boundaries.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_CATEGORY_MANIPULATION_SYSTEM = """You are an epistemic language category manipulation specialist. Given strategic classification, assess category manipulation:

Key concepts:
- Epistemic language category manipulation: strategic classification that changes judgment
- Strategic classification: choosing categories to produce desired conclusions
- Boundary gerrymandering: drawing category boundaries around convenient cases
- Lumping and splitting: combining or separating cases strategically
- Definition stretching: expanding definitions beyond warranted scope
- Classification laundering: making value choices look taxonomic
- Borderline exploitation: using ambiguous cases to shift meaning

When category manipulation IS present:
- Strategic classification used
- Boundaries gerrymandered
- Cases lumped or split selectively
- Definitions stretched
- Value choices laundered as taxonomy
- Borderlines exploited
- Conclusions driven by classification

When no category manipulation:
- Classification principled
- Boundaries consistent
- Lumping and splitting justified
- Definitions stable
- Value choices explicit
- Borderlines acknowledged
- Conclusions do not depend on category tricks

Output JSON with: category_manipulation_detected (bool), severity (none/mild/moderate/severe), strategic_classification (what classification strategic), boundary_gerrymandering (what boundary gerrymandered), lumping_splitting (what lumped or split), definition_stretching (what definition stretched), recommendation (no_category_manipulation/mild_definition_clarification/significant_boundary_review/major_intensive_taxonomy_audit/emergency_complete_category_manipulation)."""

EPISTEMIC_LANGUAGE_CATEGORY_MANIPULATION_PROMPT = """Detect epistemic language category manipulation:

Strategic classification: {strategic_classification}
Boundary gerrymandering: {boundary_gerrymandering}
Lumping/splitting: {lumping_splitting}
Definition stretching: {definition_stretching}
Domain: {domain}
Context: {context}

Is strategic classification manipulating the conclusion? Return ONLY valid JSON."""


class EpistemicLanguageCategoryManipulationService:
    """Detects epistemic language category manipulation - strategic classification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategic_classification: str,
        *,
        boundary_gerrymandering: str = "",
        lumping_splitting: str = "",
        definition_stretching: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language category manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_CATEGORY_MANIPULATION_PROMPT.format(
                strategic_classification=strategic_classification,
                boundary_gerrymandering=boundary_gerrymandering or "Not specified",
                lumping_splitting=lumping_splitting or "Not specified",
                definition_stretching=definition_stretching or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_CATEGORY_MANIPULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategic_classification": strategic_classification[:200],
            "category_manipulation_detected": data.get("category_manipulation_detected", False),
            "severity": data.get("severity", ""),
            "boundary_gerrymandering": data.get("boundary_gerrymandering", ""),
            "lumping_splitting": data.get("lumping_splitting", ""),
            "definition_stretching": data.get("definition_stretching", ""),
            "recommendation": data.get("recommendation", ""),
        }

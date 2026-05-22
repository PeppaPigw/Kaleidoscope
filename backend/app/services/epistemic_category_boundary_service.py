"""EpistemicCategoryBoundaryService — Epistemic Category Boundary Detection.

Detects epistemic category boundary imposition — imposing sharp boundaries
on fuzzy categories, creating false precision in classification.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATEGORY_BOUNDARY_SYSTEM = """You are an epistemic category boundary specialist. Given sharp boundaries imposed on fuzzy categories, assess category boundary imposition:

Key concepts:
- Epistemic category boundary: imposing sharp boundaries on fuzzy categories
- False dichotomy: creating binary where spectrum exists
- Boundary arbitrariness: arbitrary placement of category boundaries
- Sorites vulnerability: vulnerable to sorites paradox
- Borderline case denial: denying existence of borderline cases
- Precision theater: false precision in inherently fuzzy classification
- Continuum fallacy: denying real differences because boundary is fuzzy

When epistemic category boundary IS present:
- Sharp boundaries on fuzzy categories
- False dichotomies created
- Boundaries arbitrarily placed
- Sorites paradox ignored
- Borderline cases denied
- False precision imposed
- Continuum exploited or denied

When no category boundary imposition:
- Fuzziness acknowledged
- Spectrums recognized
- Boundaries justified
- Sorites considered
- Borderline cases acknowledged
- Precision appropriate
- Continuum handled appropriately

Output JSON with: category_boundary_detected (bool), severity (none/mild/moderate/severe), false_dichotomy (what false dichotomies), boundary_arbitrariness (what arbitrary boundaries), borderline_denial (what borderline cases denied), precision_theater (what false precision), recommendation (no_category_boundary/mild_fuzziness_awareness/significant_spectrum_recognition/major_intensive_boundary_dissolution/emergency_complete_category_boundary)."""

EPISTEMIC_CATEGORY_BOUNDARY_PROMPT = """Detect epistemic category boundary imposition:

False dichotomy: {false_dichotomy}
Boundary arbitrariness: {boundary_arbitrariness}
Borderline denial: {borderline_denial}
Precision theater: {precision_theater}
Domain: {domain}
Context: {context}

Are sharp boundaries being imposed on inherently fuzzy categories? Return ONLY valid JSON."""


class EpistemicCategoryBoundaryService:
    """Detects epistemic category boundary — false sharpness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        false_dichotomy: str,
        *,
        boundary_arbitrariness: str = "",
        borderline_denial: str = "",
        precision_theater: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category boundary imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATEGORY_BOUNDARY_PROMPT.format(
                false_dichotomy=false_dichotomy,
                boundary_arbitrariness=boundary_arbitrariness or "Not specified",
                borderline_denial=borderline_denial or "Not specified",
                precision_theater=precision_theater or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATEGORY_BOUNDARY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "false_dichotomy": false_dichotomy[:200],
            "category_boundary_detected": data.get("category_boundary_detected", False),
            "severity": data.get("severity", ""),
            "boundary_arbitrariness": data.get("boundary_arbitrariness", ""),
            "borderline_denial": data.get("borderline_denial", ""),
            "precision_theater": data.get("precision_theater", ""),
            "recommendation": data.get("recommendation", ""),
        }

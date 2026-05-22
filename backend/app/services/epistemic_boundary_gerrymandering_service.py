"""EpistemicBoundaryGerrymanderingService — Epistemic Boundary Gerrymandering Detection.

Detects epistemic boundary gerrymandering — drawing boundaries strategically
to include or exclude evidence that supports a preferred conclusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BOUNDARY_GERRYMANDERING_SYSTEM = """You are an epistemic boundary gerrymandering specialist. Given strategic boundary drawing, assess gerrymandering:

Key concepts:
- Epistemic boundary gerrymandering: drawing boundaries to include/exclude evidence strategically
- Category manipulation: manipulating categories to include/exclude
- Definition gaming: defining terms to include/exclude desired cases
- Time window selection: selecting time windows that support conclusion
- Population selection: selecting populations that support conclusion
- Metric selection: selecting metrics that support conclusion
- Comparison group manipulation: manipulating comparison groups

When epistemic boundary gerrymandering IS present:
- Boundaries drawn strategically
- Categories manipulated
- Definitions gamed
- Time windows selected
- Populations selected
- Metrics selected
- Comparison groups manipulated

When no boundary gerrymandering:
- Boundaries principled
- Categories natural
- Definitions standard
- Time windows justified
- Populations representative
- Metrics appropriate
- Comparison groups fair

Output JSON with: boundary_gerrymandering_detected (bool), severity (none/mild/moderate/severe), category_manipulation (what categories manipulated), definition_gaming (what definitions gamed), time_window_selection (what time windows selected), metric_selection (what metrics selected), recommendation (no_boundary_gerrymandering/mild_boundary_review/significant_principled_boundaries/major_intensive_boundary_correction/emergency_complete_gerrymandering)."""

EPISTEMIC_BOUNDARY_GERRYMANDERING_PROMPT = """Detect epistemic boundary gerrymandering:

Category manipulation: {category_manipulation}
Definition gaming: {definition_gaming}
Time window selection: {time_window_selection}
Metric selection: {metric_selection}
Domain: {domain}
Context: {context}

Are boundaries being drawn strategically to include/exclude evidence? Return ONLY valid JSON."""


class EpistemicBoundaryGerrymanderingService:
    """Detects epistemic boundary gerrymandering — strategic boundary drawing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        category_manipulation: str,
        *,
        definition_gaming: str = "",
        time_window_selection: str = "",
        metric_selection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic boundary gerrymandering."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BOUNDARY_GERRYMANDERING_PROMPT.format(
                category_manipulation=category_manipulation,
                definition_gaming=definition_gaming or "Not specified",
                time_window_selection=time_window_selection or "Not specified",
                metric_selection=metric_selection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BOUNDARY_GERRYMANDERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "category_manipulation": category_manipulation[:200],
            "boundary_gerrymandering_detected": data.get("boundary_gerrymandering_detected", False),
            "severity": data.get("severity", ""),
            "definition_gaming": data.get("definition_gaming", ""),
            "time_window_selection": data.get("time_window_selection", ""),
            "metric_selection": data.get("metric_selection", ""),
            "recommendation": data.get("recommendation", ""),
        }

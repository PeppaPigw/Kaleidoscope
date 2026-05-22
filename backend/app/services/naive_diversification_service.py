"""NaiveDiversificationService — Naive Diversification Detection.

Detects naive diversification — tendency to spread resources
equally across options regardless of their quality or expected
returns. Benartzi & Thaler (2001). "1/n heuristic" — dividing
equally among n options without analysis. Leads to suboptimal
allocation when options differ in quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NAIVE_DIVERSIFICATION_SYSTEM = """You are a naive diversification specialist. Given a resource allocation decision, assess whether someone is spreading resources equally without regard to option quality:

Key concepts (Benartzi & Thaler, 2001):
- 1/n heuristic: dividing equally among available options
- Menu dependence: allocation changes with option set, not fundamentals
- Diversification bias: over-diversifying when concentration is optimal
- Variety seeking: choosing variety for its own sake
- Choice architecture effect: allocation driven by how options are presented
- Equal weighting fallacy: treating all options as equally worthy
- Partition dependence interaction: how categories are divided affects allocation

When naive diversification IS present:
- Splitting investment equally across all available funds
- "A little of everything" without analyzing relative merits
- Allocation that would change if options were grouped differently
- Equal time/money/effort across projects of vastly different value
- Diversifying when concentration on best option is clearly superior
- "I'll try all of them" when some are clearly better than others

When equal allocation IS rational:
- Options are genuinely similar in expected value
- True uncertainty makes differentiation impossible
- Diversification reduces genuine risk (portfolio theory)
- The cost of analysis exceeds the benefit of optimization
- Equal allocation is a deliberate strategy, not a default

Output JSON with: naive_diversification_present (bool), severity (none/mild/moderate/severe), decision (what allocation is being made), options (what options are available), allocation (how are resources being allocated), quality_difference (how much do options differ in quality?), menu_dependent (would allocation change with different option set?), analysis_performed (was relative quality analyzed?), optimal_allocation (what would informed allocation look like?), recommendation (allocation_rational/mild_naive_spread/significant_quality_ignored/major_naive_diversification/analyze_relative_merit)."""

NAIVE_DIVERSIFICATION_PROMPT = """Detect naive diversification:

Decision: {decision}
Options: {options}
Allocation: {allocation}
Analysis: {analysis}
Domain: {domain}
Context: {context}

Is someone spreading resources equally without regard to option quality? Return ONLY valid JSON."""


class NaiveDiversificationService:
    """Detects naive diversification — equal spreading without quality analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        options: str = "",
        allocation: str = "",
        analysis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect naive diversification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NAIVE_DIVERSIFICATION_PROMPT.format(
                decision=decision,
                options=options or "Not specified",
                allocation=allocation or "Not specified",
                analysis=analysis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NAIVE_DIVERSIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "naive_diversification_present": data.get("naive_diversification_present", False),
            "severity": data.get("severity", ""),
            "quality_difference": data.get("quality_difference", ""),
            "menu_dependent": data.get("menu_dependent", ""),
            "analysis_performed": data.get("analysis_performed", ""),
            "optimal_allocation": data.get("optimal_allocation", ""),
            "recommendation": data.get("recommendation", ""),
        }

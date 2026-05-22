"""NaiveAllocationService — Naive Allocation Detection.

Detects naive allocation — the tendency to divide resources equally
(1/N heuristic) regardless of differential need, merit, or
efficiency. Benartzi & Thaler (2001). Equal division feels fair
but can be deeply unfair when circumstances differ. The equality
heuristic substitutes for the harder work of proportional justice.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NAIVE_ALLOCATION_SYSTEM = """You are a naive allocation specialist. Given a resource distribution decision, assess whether equal division is being applied inappropriately:

Key concepts (Benartzi & Thaler, 2001):
- Naive allocation: 1/N heuristic regardless of circumstances
- Equality heuristic: equal = fair (but not always)
- Equity vs equality: proportional to contribution vs same for all
- Need-based allocation: proportional to need
- Efficiency allocation: where resources produce most value
- Diversification heuristic: spreading evenly across options
- Partition dependence: allocation depends on how options are grouped

When naive allocation IS problematic:
- Equal budget splits when needs differ dramatically
- Equal time allocation when tasks have different importance
- Equal attention to all options when some are clearly better
- "Fair share" meaning equal share regardless of contribution
- Equal investment across all projects regardless of potential
- Splitting resources evenly to avoid the harder decision
- Equal treatment when equity demands differential treatment

When equal allocation IS appropriate:
- Genuine uncertainty about differential value
- Rights-based contexts where equality is the principle
- Transaction costs of differential allocation exceed benefits
- Information is insufficient to justify unequal distribution
- The domain genuinely calls for equal treatment
- Differential allocation would create perverse incentives

Output JSON with: naive_allocation_present (bool), severity (none/mild/moderate/severe), resource (what is being allocated), allocation_method (how is it being divided), differential_factors (what factors suggest unequal allocation), equality_justification (why equal seems fair), better_allocation (what would be more appropriate), avoidance_motive (is equal division avoiding a harder decision), recommendation (equal_allocation_appropriate/mild_naive_division/significant_naive_allocation/major_equality_as_avoidance/allocate_proportionally)."""

NAIVE_ALLOCATION_PROMPT = """Detect naive allocation:

Decision: {decision}
Resources: {resources}
Recipients: {recipients}
Differences: {differences}
Domain: {domain}
Context: {context}

Is equal division being applied inappropriately when circumstances call for differential allocation? Return ONLY valid JSON."""


class NaiveAllocationService:
    """Detects naive allocation — inappropriate equal division of resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        resources: str = "",
        recipients: str = "",
        differences: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect naive allocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NAIVE_ALLOCATION_PROMPT.format(
                decision=decision,
                resources=resources or "Not specified",
                recipients=recipients or "Not specified",
                differences=differences or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NAIVE_ALLOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "naive_allocation_present": data.get("naive_allocation_present", False),
            "severity": data.get("severity", ""),
            "resource": data.get("resource", ""),
            "allocation_method": data.get("allocation_method", ""),
            "differential_factors": data.get("differential_factors", ""),
            "equality_justification": data.get("equality_justification", ""),
            "better_allocation": data.get("better_allocation", ""),
            "avoidance_motive": data.get("avoidance_motive", ""),
            "recommendation": data.get("recommendation", ""),
        }

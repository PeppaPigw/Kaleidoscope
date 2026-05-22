"""SimplicityFetishService — Simplicity Fetish Detection.

Detects simplicity fetish — fetishizing simplicity at the cost
of accuracy, preferring simple but wrong over complex but right.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SIMPLICITY_FETISH_SYSTEM = """You are a simplicity fetish specialist. Given an explanation preference, assess whether simplicity is being fetishized at the cost of accuracy:

Key concepts:
- Simplicity fetish: fetishizing simplicity over accuracy
- Oversimplification worship: worshipping oversimplification
- Complexity aversion: aversion to necessary complexity
- Reductionism excess: excessive reductionism losing essential detail
- Sound-bite preference: preferring sound bites over nuance
- False simplicity: imposing false simplicity on complex reality
- Occam's razor abuse: misusing parsimony principle

When simplicity fetish IS present:
- Simplicity fetishized at cost of accuracy
- Oversimplification preferred over nuanced truth
- Necessary complexity rejected
- Essential detail lost through excessive reduction
- Sound bites preferred over accurate explanation
- False simplicity imposed on complex reality
- Parsimony principle misused to reject complexity

When appropriate simplicity is present:
- Simplicity preferred when equally accurate
- Complexity accepted when necessary
- Detail preserved when essential
- Nuance maintained when important
- Simplification appropriate to audience
- Parsimony applied correctly
- Complexity proportionate to subject

Output JSON with: fetish_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is preferred), simplification (how it is oversimplified), lost_accuracy (what accuracy is lost), necessary_complexity (what complexity is needed), recommendation (appropriate_simplicity/mild_oversimplification/significant_simplicity_fetish/major_accuracy_sacrifice/accept_necessary_complexity)."""

SIMPLICITY_FETISH_PROMPT = """Detect simplicity fetish:

Explanation: {explanation}
Simplification: {simplification}
Lost accuracy: {lost}
Necessary complexity: {complexity}
Domain: {domain}
Context: {context}

Is simplicity being fetishized at the cost of accuracy? Return ONLY valid JSON."""


class SimplicityFetishService:
    """Detects simplicity fetish — fetishizing simplicity over accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        simplification: str = "",
        lost: str = "",
        complexity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect simplicity fetish."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SIMPLICITY_FETISH_PROMPT.format(
                explanation=explanation,
                simplification=simplification or "Not specified",
                lost=lost or "Not specified",
                complexity=complexity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SIMPLICITY_FETISH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "fetish_present": data.get("fetish_present", False),
            "severity": data.get("severity", ""),
            "simplification": data.get("simplification", ""),
            "lost_accuracy": data.get("lost_accuracy", ""),
            "necessary_complexity": data.get("necessary_complexity", ""),
            "recommendation": data.get("recommendation", ""),
        }

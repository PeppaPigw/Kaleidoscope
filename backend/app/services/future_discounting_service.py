"""FutureDiscountingService — Future Discounting Detection.

Detects epistemic future discounting — systematically undervaluing
future epistemic consequences, where short-term knowledge gains
are prioritized over long-term understanding costs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FUTURE_DISCOUNTING_SYSTEM = """You are an epistemic future discounting specialist. Given a decision, assess whether future epistemic consequences are being systematically undervalued:

Key concepts:
- Future discounting: undervaluing future epistemic consequences
- Short-termism: prioritizing immediate knowledge over long-term
- Understanding debt: accumulating future understanding costs
- Epistemic myopia: seeing only near-term knowledge effects
- Deferred costs: pushing epistemic costs to the future
- Temporal bias: present knowledge valued over future
- Sustainability neglect: ignoring long-term knowledge health

When future discounting IS present:
- Future epistemic consequences systematically undervalued
- Short-term knowledge gains prioritized over long-term costs
- Understanding debt accumulated without acknowledgment
- Long-term knowledge effects ignored
- Present convenience prioritized over future understanding
- Epistemic sustainability not considered
- Deferred costs not accounted for

When present focus is appropriate:
- Immediate knowledge needs genuinely urgent
- Future consequences acknowledged even if deferred
- Trade-offs between present and future explicit
- Long-term costs estimated and accepted
- Sustainability considered even if not prioritized
- Temporal trade-offs justified by context
- Future epistemic health not permanently damaged

Output JSON with: discounting_present (bool), severity (none/mild/moderate/severe), decision (what decision is made), short_term_gain (what immediate benefit), long_term_cost (what future cost), discount_rate (how much future is undervalued), recommendation (appropriate_temporal_priority/mild_future_neglect/significant_future_discounting/major_epistemic_myopia/value_future_understanding)."""

FUTURE_DISCOUNTING_PROMPT = """Detect epistemic future discounting:

Decision: {decision}
Short-term benefit: {short_term}
Long-term consequence: {long_term}
Justification: {justification}
Domain: {domain}
Context: {context}

Are future epistemic consequences being systematically undervalued? Return ONLY valid JSON."""


class FutureDiscountingService:
    """Detects epistemic future discounting — undervaluing future consequences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        short_term: str = "",
        long_term: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic future discounting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FUTURE_DISCOUNTING_PROMPT.format(
                decision=decision,
                short_term=short_term or "Not specified",
                long_term=long_term or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FUTURE_DISCOUNTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "discounting_present": data.get("discounting_present", False),
            "severity": data.get("severity", ""),
            "short_term_gain": data.get("short_term_gain", ""),
            "long_term_cost": data.get("long_term_cost", ""),
            "discount_rate": data.get("discount_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }

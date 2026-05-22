"""WillfulIgnoranceStrategicService — Strategic Willful Ignorance Detection.

Detects strategic willful ignorance — deliberately avoiding information
that would create obligations, responsibilities, or uncomfortable
knowledge, where not-knowing is strategically maintained.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WILLFUL_IGNORANCE_STRATEGIC_SYSTEM = """You are a strategic willful ignorance specialist. Given a situation, assess whether ignorance is being strategically maintained:

Key concepts:
- Strategic willful ignorance: deliberately avoiding information
- Plausible deniability: not knowing to avoid responsibility
- Information avoidance: actively avoiding available information
- Obligation avoidance: not knowing to avoid obligations
- Convenient ignorance: ignorance that serves interests
- Knowledge refusal: refusing to learn what's available
- Strategic not-knowing: ignorance as strategy

When strategic willful ignorance IS present:
- Information deliberately avoided
- Not-knowing serves strategic interests
- Available information actively refused
- Ignorance maintained to avoid obligations
- Plausible deniability cultivated
- Convenient ignorance about inconvenient facts
- Knowledge refused because it would create responsibility

When information avoidance is appropriate:
- Information genuinely unavailable
- Privacy boundaries respected
- Information overload managed
- Scope appropriately bounded
- Delegation with appropriate trust
- Information not relevant to responsibilities
- Boundaries serve legitimate purposes

Output JSON with: willful_present (bool), severity (none/mild/moderate/severe), situation (what situation is analyzed), information_avoided (what information is avoided), obligation_avoided (what obligation would arise), strategy (how ignorance is maintained), recommendation (appropriate_information_boundaries/mild_avoidance/significant_willful_ignorance/major_strategic_not_knowing/accept_information_and_obligations)."""

WILLFUL_IGNORANCE_STRATEGIC_PROMPT = """Detect strategic willful ignorance:

Situation: {situation}
Information available: {available}
Information avoided: {avoided}
Obligation at stake: {obligation}
Domain: {domain}
Context: {context}

Is ignorance being strategically maintained to avoid obligations? Return ONLY valid JSON."""


class WillfulIgnoranceStrategicService:
    """Detects strategic willful ignorance — deliberately avoiding information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        available: str = "",
        avoided: str = "",
        obligation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic willful ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WILLFUL_IGNORANCE_STRATEGIC_PROMPT.format(
                situation=situation,
                available=available or "Not specified",
                avoided=avoided or "Not specified",
                obligation=obligation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WILLFUL_IGNORANCE_STRATEGIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "willful_present": data.get("willful_present", False),
            "severity": data.get("severity", ""),
            "information_avoided": data.get("information_avoided", ""),
            "obligation_avoided": data.get("obligation_avoided", ""),
            "strategy": data.get("strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }

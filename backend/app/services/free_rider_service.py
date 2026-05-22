"""FreeRiderService — Free Rider Problem Detection.

Detects free rider problem — when individuals benefit from
collective action or public goods without contributing their
fair share, potentially undermining the collective effort
if the behavior becomes widespread.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FREE_RIDER_SYSTEM = """You are a free rider problem specialist. Given a situation, assess whether free riding is occurring or being enabled:

Key concepts:
- Free rider: benefiting from collective goods without contributing
- Public goods: non-excludable, non-rivalrous resources
- Tragedy of the commons: overuse of shared resources
- Collective action problem: individual incentives vs group welfare
- Excludability: can non-contributors be prevented from benefiting?
- Contribution threshold: minimum participation needed for provision
- Social loafing: reduced effort in group settings

When free riding IS present:
- Benefiting from team effort without contributing proportionally
- Using shared resources without maintaining them
- Enjoying public goods while avoiding taxes/contributions
- Relying on others' vaccination while refusing one's own
- Taking credit for collective achievements without participation
- Consuming open-source without contributing back
- Exploiting others' cooperation while defecting

When free riding is NOT present:
- Contributions are proportional to benefits received
- Non-contribution is due to inability, not choice
- The good is genuinely non-rivalrous (use doesn't diminish it)
- Mechanisms exist to ensure fair contribution
- The person contributes in other ways not immediately visible
- The situation involves legitimate specialization of roles
- Exclusion mechanisms prevent non-contributors from benefiting

Output JSON with: free_rider_present (bool), severity (none/mild/moderate/severe), benefit (what is being gained), contribution (what is not being contributed), collective_good (what shared resource is involved), sustainability (is the arrangement sustainable), mechanism (what enables the free riding), recommendation (no_free_riding/mild_imbalance/significant_free_riding/major_exploitation/design_contribution_mechanisms)."""

FREE_RIDER_PROMPT = """Detect free rider problem:

Situation: {situation}
Benefits received: {benefits}
Contributions made: {contributions}
Collective good: {collective_good}
Domain: {domain}
Context: {context}

Is someone benefiting from collective action without contributing their fair share? Return ONLY valid JSON."""


class FreeRiderService:
    """Detects free rider problem — benefiting without contributing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        benefits: str = "",
        contributions: str = "",
        collective_good: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect free rider problem."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FREE_RIDER_PROMPT.format(
                situation=situation,
                benefits=benefits or "Not specified",
                contributions=contributions or "Not specified",
                collective_good=collective_good or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FREE_RIDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "free_rider_present": data.get("free_rider_present", False),
            "severity": data.get("severity", ""),
            "benefit": data.get("benefit", ""),
            "contribution": data.get("contribution", ""),
            "sustainability": data.get("sustainability", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicAddictionService — Epistemic Addiction Detection.

Detects epistemic addiction — compulsive engagement with specific
types of information regardless of utility or harm.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ADDICTION_SYSTEM = """You are an epistemic addiction specialist. Given an information engagement pattern, assess whether compulsive engagement occurs regardless of utility:

Key concepts:
- Epistemic addiction: compulsive engagement with specific information
- Compulsive consumption: consuming information compulsively
- Utility independence: engagement regardless of utility
- Dopamine-driven: engagement driven by reward not value
- Tolerance building: needing more for same satisfaction
- Withdrawal: discomfort when deprived of information type
- Harm despite awareness: continuing despite known harm

When epistemic addiction IS present:
- Compulsive engagement with specific information types
- Consuming information compulsively regardless of utility
- Engagement driven by reward rather than value
- Needing increasing amounts for same satisfaction
- Discomfort when deprived of the information type
- Continuing engagement despite known harm
- Unable to stop despite wanting to

When healthy engagement is present:
- Engagement proportionate to utility
- Information consumption driven by need
- Engagement driven by genuine value
- Satisfaction from appropriate amounts
- Comfortable without constant information
- Stopping when engagement becomes harmful
- Able to disengage when appropriate

Output JSON with: addiction_present (bool), severity (none/mild/moderate/severe), information_type (what information is addictive), compulsion (what compulsion exists), harm (what harm results), utility_disconnect (how disconnected from utility), recommendation (healthy_engagement/mild_overconsumption/significant_addiction/major_compulsive_engagement/restore_utility_driven_engagement)."""

EPISTEMIC_ADDICTION_PROMPT = """Detect epistemic addiction:

Information type: {information_type}
Compulsion: {compulsion}
Harm: {harm}
Utility disconnect: {utility_disconnect}
Domain: {domain}
Context: {context}

Is compulsive engagement with specific information occurring regardless of utility? Return ONLY valid JSON."""


class EpistemicAddictionService:
    """Detects epistemic addiction — compulsive information engagement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_type: str,
        *,
        compulsion: str = "",
        harm: str = "",
        utility_disconnect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ADDICTION_PROMPT.format(
                information_type=information_type,
                compulsion=compulsion or "Not specified",
                harm=harm or "Not specified",
                utility_disconnect=utility_disconnect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_type": information_type[:200],
            "addiction_present": data.get("addiction_present", False),
            "severity": data.get("severity", ""),
            "compulsion": data.get("compulsion", ""),
            "harm": data.get("harm", ""),
            "utility_disconnect": data.get("utility_disconnect", ""),
            "recommendation": data.get("recommendation", ""),
        }

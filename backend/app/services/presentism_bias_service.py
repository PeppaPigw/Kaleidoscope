"""PresentismBiasService — Presentism Bias Detection.

Detects presentism bias — applying current moral, cultural, or
intellectual standards to judge historical actions, beliefs, or
institutions without accounting for the norms and knowledge of
their time period.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRESENTISM_BIAS_SYSTEM = """You are a presentism bias specialist. Given a judgment about historical actions, assess whether current standards are being anachronistically applied:

Key concepts:
- Presentism: judging the past by present standards
- Anachronism: applying concepts from one era to another
- Moral progress: acknowledging change without condemning all predecessors
- Contextual ethics: understanding moral reasoning within its time
- Charitable interpretation: understanding before judging
- Temporal chauvinism: assuming current views are obviously correct
- Historical empathy: understanding past perspectives on their own terms

When presentism IS present:
- Condemning historical figures for not holding modern views
- "How could they not see that X was wrong?" when X was universal then
- Applying current scientific knowledge to judge past medical practices
- Judging past institutions by standards that didn't exist yet
- Assuming current moral consensus was always obvious
- Ignoring that moral progress required people working within their context
- Treating historical norms as individual moral failures

When current standards ARE appropriately applied:
- Contemporary critics existed and raised the same objections
- The person violated their own stated principles
- The judgment acknowledges historical context while noting harm
- Universal moral principles (not culturally specific ones) are invoked
- The purpose is understanding patterns, not condemning individuals
- The analysis distinguishes between what was known and what was done
- The judgment is about systems and structures, not individual blame

Output JSON with: presentism_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is made), historical_context (what was normal then), current_standard (what standard is applied), anachronism (what is anachronistic), contemporary_critics (did critics exist at the time), recommendation (judgment_appropriate/mild_presentism/significant_anachronistic_judgment/major_temporal_chauvinism/consider_historical_context)."""

PRESENTISM_BIAS_PROMPT = """Detect presentism bias:

Judgment: {judgment}
Historical context: {historical_context}
Standard applied: {standard}
Time period: {time_period}
Domain: {domain}
Context: {context}

Is this judgment anachronistically applying current standards to the past? Return ONLY valid JSON."""


class PresentismBiasService:
    """Detects presentism bias — anachronistic application of current standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        historical_context: str = "",
        standard: str = "",
        time_period: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect presentism bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRESENTISM_BIAS_PROMPT.format(
                judgment=judgment,
                historical_context=historical_context or "Not specified",
                standard=standard or "Not specified",
                time_period=time_period or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRESENTISM_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "presentism_present": data.get("presentism_present", False),
            "severity": data.get("severity", ""),
            "historical_context": data.get("historical_context", ""),
            "current_standard": data.get("current_standard", ""),
            "anachronism": data.get("anachronism", ""),
            "contemporary_critics": data.get("contemporary_critics", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicHibernationService — Epistemic Hibernation Detection.

Detects epistemic hibernation — ideas entering deep dormancy to
survive intellectual winters, dramatically reducing activity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HIBERNATION_SYSTEM = """You are an epistemic hibernation specialist. Given an idea dormancy pattern, assess whether ideas enter deep dormancy to survive hostile periods:

Key concepts:
- Epistemic hibernation: ideas entering deep dormancy
- Intellectual winter: hostile period requiring dormancy
- Metabolic reduction: dramatic reduction in intellectual activity
- Fat reserves: stored intellectual energy for dormancy
- Arousal: periodic brief awakenings during hibernation
- Spring emergence: ideas reactivating when conditions improve
- Torpor: state of minimal intellectual activity

When epistemic hibernation IS present:
- Ideas entering deep dormancy to survive hostile periods
- Hostile intellectual period requiring reduced activity
- Dramatic reduction in intellectual activity
- Stored intellectual energy sustaining dormancy
- Periodic brief awakenings during dormant period
- Potential for reactivation when conditions improve
- State of minimal intellectual activity maintained

When active ideas are present:
- Ideas remaining fully active
- No hostile period requiring dormancy
- Full intellectual activity maintained
- No need for stored energy reserves
- Continuous activity without dormant periods
- No waiting for conditions to improve
- Full intellectual metabolism maintained

Output JSON with: hibernation_present (bool), severity (none/mild/moderate/severe), ideas (what ideas hibernate), winter (what hostile period triggers it), reserves (what stored energy sustains), emergence (when/how ideas will reactivate), recommendation (active_ideas/mild_slowdown/significant_hibernation/major_deep_dormancy/prepare_for_spring_emergence)."""

EPISTEMIC_HIBERNATION_PROMPT = """Detect epistemic hibernation:

Ideas: {ideas}
Winter: {winter}
Reserves: {reserves}
Emergence: {emergence}
Domain: {domain}
Context: {context}

Are ideas entering deep dormancy to survive intellectual winters with dramatically reduced activity? Return ONLY valid JSON."""


class EpistemicHibernationService:
    """Detects epistemic hibernation — deep idea dormancy during hostile periods."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        winter: str = "",
        reserves: str = "",
        emergence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hibernation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HIBERNATION_PROMPT.format(
                ideas=ideas,
                winter=winter or "Not specified",
                reserves=reserves or "Not specified",
                emergence=emergence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HIBERNATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "hibernation_present": data.get("hibernation_present", False),
            "severity": data.get("severity", ""),
            "winter": data.get("winter", ""),
            "reserves": data.get("reserves", ""),
            "emergence": data.get("emergence", ""),
            "recommendation": data.get("recommendation", ""),
        }

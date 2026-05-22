"""ApexFallacyService — Apex Fallacy Detection.

Detects the apex fallacy — judging an entire group by its most
visible, extreme, or successful members. The top of any
distribution is not representative of the whole. Judging "men"
by CEOs, "immigrants" by criminals, or "scientists" by Nobel
laureates ignores the vast majority who are unremarkable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APEX_FALLACY_SYSTEM = """You are an apex fallacy specialist. Given a generalization about a group, assess whether the group is being judged by its most visible or extreme members:

Key concepts:
- Apex fallacy: judging a group by its top/extreme members
- Visibility bias: extreme members are most visible
- Distribution ignorance: ignoring the shape of the full distribution
- Representativeness error: assuming extremes represent the whole
- Survivorship bias interaction: only seeing those who made it to the top
- Media selection bias: news covers extremes, not averages
- Ecological fallacy variant: group-level extremes applied to individuals

When apex fallacy IS present:
- Judging a profession by its most famous practitioners
- Generalizing about a demographic from its most visible members
- "Men are powerful" (based on CEOs, ignoring homeless men)
- "Immigrants are dangerous" (based on criminals, ignoring majority)
- Using extreme examples as representative of the whole group
- Policy based on extreme cases rather than typical cases
- "That group has it easy" based on most successful members

When extreme examples ARE relevant:
- The discussion is specifically about the extremes
- The distribution is acknowledged alongside the examples
- Extreme cases reveal systemic patterns (not just individual luck)
- The generalization is about possibility, not typicality
- Base rates are provided alongside extreme examples
- The argument doesn't claim extremes are representative

Output JSON with: apex_fallacy_present (bool), severity (none/mild/moderate/severe), group (what group is being characterized), apex_members (who are the extreme members cited), actual_distribution (what does the full distribution look like), representativeness (how representative are the cited members), visibility_bias (why are these members most visible), base_rate (what is the typical member like), recommendation (characterization_fair/mild_apex_bias/significant_apex_fallacy/major_distribution_ignorance/consider_full_distribution)."""

APEX_FALLACY_PROMPT = """Detect apex fallacy:

Generalization: {generalization}
Group: {group}
Examples cited: {examples}
Distribution: {distribution}
Domain: {domain}
Context: {context}

Is a group being judged by its most visible or extreme members rather than its typical members? Return ONLY valid JSON."""


class ApexFallacyService:
    """Detects apex fallacy — judging groups by their extreme members."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        generalization: str,
        *,
        group: str = "",
        examples: str = "",
        distribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect apex fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APEX_FALLACY_PROMPT.format(
                generalization=generalization,
                group=group or "Not specified",
                examples=examples or "Not specified",
                distribution=distribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APEX_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "generalization": generalization[:200],
            "apex_fallacy_present": data.get("apex_fallacy_present", False),
            "severity": data.get("severity", ""),
            "group": data.get("group", ""),
            "apex_members": data.get("apex_members", ""),
            "actual_distribution": data.get("actual_distribution", ""),
            "representativeness": data.get("representativeness", ""),
            "visibility_bias": data.get("visibility_bias", ""),
            "base_rate": data.get("base_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }

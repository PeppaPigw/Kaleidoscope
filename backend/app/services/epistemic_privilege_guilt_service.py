"""EpistemicPrivilegeGuiltService — Epistemic Privilege Guilt Detection.

Detects epistemic privilege guilt — guilt over having intellectual
advantages that others lack.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRIVILEGE_GUILT_SYSTEM = """You are an epistemic privilege guilt specialist. Given guilt over intellectual advantages, assess privilege guilt:

Key concepts:
- Epistemic privilege guilt: guilt over intellectual advantages
- Access guilt: guilt about educational opportunities others lack
- Talent guilt: guilt about natural cognitive abilities
- Resource guilt: guilt about having research resources
- Network guilt: guilt about intellectual connections
- Opportunity guilt: guilt about chances others never had
- Unearned advantage: feeling success is undeserved

When epistemic privilege guilt IS present:
- Guilt over intellectual advantages
- Guilt about opportunities
- Guilt about abilities
- Guilt about resources
- Guilt about connections
- Guilt about chances
- Feeling undeserved

When no privilege guilt:
- Grateful without guilt
- Using advantages well
- Comfortable with abilities
- Sharing resources
- Leveraging connections for good
- Making most of chances
- Earned confidence

Output JSON with: privilege_guilt_detected (bool), severity (none/mild/moderate/severe), access_guilt (what feeling guilty about), talent_guilt (what abilities causing guilt), resource_guilt (what resources feeling guilty about), opportunity_guilt (what chances causing guilt), recommendation (no_privilege_guilt/mild_gratitude_practice/significant_purpose_building/major_intensive_guilt_processing/emergency_paralyzing_guilt)."""

EPISTEMIC_PRIVILEGE_GUILT_PROMPT = """Detect epistemic privilege guilt:

Access guilt: {access_guilt}
Talent guilt: {talent_guilt}
Resource guilt: {resource_guilt}
Opportunity guilt: {opportunity_guilt}
Domain: {domain}
Context: {context}

Is there guilt over having intellectual advantages others lack? Return ONLY valid JSON."""


class EpistemicPrivilegeGuiltService:
    """Detects epistemic privilege guilt — guilt over intellectual advantages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        access_guilt: str,
        *,
        talent_guilt: str = "",
        resource_guilt: str = "",
        opportunity_guilt: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic privilege guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRIVILEGE_GUILT_PROMPT.format(
                access_guilt=access_guilt,
                talent_guilt=talent_guilt or "Not specified",
                resource_guilt=resource_guilt or "Not specified",
                opportunity_guilt=opportunity_guilt or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRIVILEGE_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "access_guilt": access_guilt[:200],
            "privilege_guilt_detected": data.get("privilege_guilt_detected", False),
            "severity": data.get("severity", ""),
            "talent_guilt": data.get("talent_guilt", ""),
            "resource_guilt": data.get("resource_guilt", ""),
            "opportunity_guilt": data.get("opportunity_guilt", ""),
            "recommendation": data.get("recommendation", ""),
        }

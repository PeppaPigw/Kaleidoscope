"""EpistemicKnowledgeHoardingMotivationService — Epistemic Knowledge Hoarding Motivation Detection.

Detects epistemic knowledge hoarding motivation — motivated to acquire
knowledge for power/status rather than understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KNOWLEDGE_HOARDING_MOTIVATION_SYSTEM = """You are an epistemic knowledge hoarding motivation specialist. Given knowledge acquisition for power, assess hoarding motivation:

Key concepts:
- Epistemic knowledge hoarding motivation: acquiring for power not understanding
- Knowledge as weapon: collecting knowledge to use against others
- Status accumulation: learning to appear superior
- Information gatekeeping: hoarding to control access
- Intellectual territory: claiming knowledge domains as property
- Power through knowing: using knowledge for dominance
- Understanding deficit: much knowledge but little comprehension

When epistemic knowledge hoarding motivation IS present:
- Acquiring for power not understanding
- Collecting to use against others
- Learning to appear superior
- Hoarding to control access
- Claiming domains as property
- Using knowledge for dominance
- Much knowledge little comprehension

When no knowledge hoarding motivation:
- Acquiring for understanding
- Sharing freely
- Learning for growth
- Open access
- Knowledge as commons
- Knowledge for service
- Deep comprehension

Output JSON with: knowledge_hoarding_motivation_detected (bool), severity (none/mild/moderate/severe), knowledge_as_weapon (what collecting to use against), status_accumulation (what learning to appear superior about), information_gatekeeping (what hoarding to control), power_through_knowing (what using for dominance), recommendation (no_knowledge_hoarding/mild_sharing_practice/significant_motivation_realignment/major_intensive_generosity_work/emergency_complete_knowledge_weaponization)."""

EPISTEMIC_KNOWLEDGE_HOARDING_MOTIVATION_PROMPT = """Detect epistemic knowledge hoarding motivation:

Knowledge as weapon: {knowledge_as_weapon}
Status accumulation: {status_accumulation}
Information gatekeeping: {information_gatekeeping}
Power through knowing: {power_through_knowing}
Domain: {domain}
Context: {context}

Is there motivation to acquire knowledge for power/status rather than understanding? Return ONLY valid JSON."""


class EpistemicKnowledgeHoardingMotivationService:
    """Detects epistemic knowledge hoarding motivation — acquiring for power not understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_as_weapon: str,
        *,
        status_accumulation: str = "",
        information_gatekeeping: str = "",
        power_through_knowing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic knowledge hoarding motivation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KNOWLEDGE_HOARDING_MOTIVATION_PROMPT.format(
                knowledge_as_weapon=knowledge_as_weapon,
                status_accumulation=status_accumulation or "Not specified",
                information_gatekeeping=information_gatekeeping or "Not specified",
                power_through_knowing=power_through_knowing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KNOWLEDGE_HOARDING_MOTIVATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_as_weapon": knowledge_as_weapon[:200],
            "knowledge_hoarding_motivation_detected": data.get("knowledge_hoarding_motivation_detected", False),
            "severity": data.get("severity", ""),
            "status_accumulation": data.get("status_accumulation", ""),
            "information_gatekeeping": data.get("information_gatekeeping", ""),
            "power_through_knowing": data.get("power_through_knowing", ""),
            "recommendation": data.get("recommendation", ""),
        }

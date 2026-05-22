"""IntellectualOutsourcingService — Intellectual Outsourcing Detection.

Detects intellectual outsourcing — outsourcing all thinking to
authorities without genuine engagement or understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_OUTSOURCING_SYSTEM = """You are an intellectual outsourcing specialist. Given a belief-formation pattern, assess whether thinking is being outsourced without engagement:

Key concepts:
- Intellectual outsourcing: outsourcing thinking without engagement
- Authority delegation: delegating all thinking to authorities
- Understanding bypass: bypassing understanding for conclusions
- Belief adoption: adopting beliefs without comprehension
- Reasoning abdication: abdicating reasoning responsibility
- Expert worship: worshipping experts without engaging ideas
- Conclusion importing: importing conclusions without understanding

When intellectual outsourcing IS present:
- All thinking outsourced to authorities
- Understanding bypassed in favor of conclusions
- Beliefs adopted without comprehension
- Reasoning responsibility abdicated
- Experts worshipped without engaging their ideas
- Conclusions imported without understanding basis
- No genuine engagement with the thinking

When appropriate expert consultation is present:
- Experts consulted while maintaining engagement
- Understanding sought alongside expert opinion
- Beliefs formed through comprehension
- Reasoning engaged with even when consulting
- Expert ideas engaged with critically
- Conclusions understood not just adopted
- Genuine engagement with the thinking

Output JSON with: outsourcing_present (bool), severity (none/mild/moderate/severe), pattern (what outsourcing pattern exists), authority (what authority is relied on), engagement (what engagement exists), understanding (what understanding exists), recommendation (appropriate_consultation/mild_delegation/significant_intellectual_outsourcing/major_reasoning_abdication/engage_with_thinking)."""

INTELLECTUAL_OUTSOURCING_PROMPT = """Detect intellectual outsourcing:

Pattern: {pattern}
Authority relied on: {authority}
Engagement level: {engagement}
Understanding: {understanding}
Domain: {domain}
Context: {context}

Is thinking being outsourced without genuine engagement? Return ONLY valid JSON."""


class IntellectualOutsourcingService:
    """Detects intellectual outsourcing — outsourcing thinking without engagement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        authority: str = "",
        engagement: str = "",
        understanding: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual outsourcing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_OUTSOURCING_PROMPT.format(
                pattern=pattern,
                authority=authority or "Not specified",
                engagement=engagement or "Not specified",
                understanding=understanding or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_OUTSOURCING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "outsourcing_present": data.get("outsourcing_present", False),
            "severity": data.get("severity", ""),
            "authority": data.get("authority", ""),
            "engagement": data.get("engagement", ""),
            "understanding": data.get("understanding", ""),
            "recommendation": data.get("recommendation", ""),
        }

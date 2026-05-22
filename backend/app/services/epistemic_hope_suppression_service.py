"""EpistemicHopeSuppressionService — Epistemic Hope Suppression Detection.

Detects epistemic hope suppression — suppressing intellectual hope
to avoid the pain of disappointment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOPE_SUPPRESSION_SYSTEM = """You are an epistemic hope suppression specialist. Given suppressing hope to avoid disappointment, assess hope suppression:

Key concepts:
- Epistemic hope suppression: suppressing hope to avoid disappointment
- Preemptive pessimism: expecting worst to avoid being let down
- Hope prohibition: forbidding self from hoping
- Disappointment avoidance: not hoping to not be disappointed
- Learned hopelessness: past disappointments killing hope
- Cynicism as protection: using cynicism to shield from hope
- Emotional flattening: suppressing hope flattening all feeling

When epistemic hope suppression IS present:
- Suppressing hope to avoid disappointment
- Expecting worst preemptively
- Forbidding self from hoping
- Not hoping to avoid disappointment
- Past disappointments killing hope
- Using cynicism as shield
- Suppressing flattening feeling

When no hope suppression:
- Hope expressed freely
- Realistic expectations
- Allowing self to hope
- Hoping despite risk
- Past not killing hope
- Genuine engagement
- Full emotional range

Output JSON with: hope_suppression_detected (bool), severity (none/mild/moderate/severe), preemptive_pessimism (what expecting worst about), hope_prohibition (what forbidding hoping about), disappointment_avoidance (what not hoping about), cynicism_as_protection (what using cynicism about), recommendation (no_hope_suppression/mild_hope_permission/significant_hope_rebuilding/major_intensive_hope_restoration/emergency_complete_hopelessness)."""

EPISTEMIC_HOPE_SUPPRESSION_PROMPT = """Detect epistemic hope suppression:

Preemptive pessimism: {preemptive_pessimism}
Hope prohibition: {hope_prohibition}
Disappointment avoidance: {disappointment_avoidance}
Cynicism as protection: {cynicism_as_protection}
Domain: {domain}
Context: {context}

Is there suppressing intellectual hope to avoid disappointment? Return ONLY valid JSON."""


class EpistemicHopeSuppressionService:
    """Detects epistemic hope suppression — suppressing hope to avoid disappointment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        preemptive_pessimism: str,
        *,
        hope_prohibition: str = "",
        disappointment_avoidance: str = "",
        cynicism_as_protection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hope suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOPE_SUPPRESSION_PROMPT.format(
                preemptive_pessimism=preemptive_pessimism,
                hope_prohibition=hope_prohibition or "Not specified",
                disappointment_avoidance=disappointment_avoidance or "Not specified",
                cynicism_as_protection=cynicism_as_protection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOPE_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "preemptive_pessimism": preemptive_pessimism[:200],
            "hope_suppression_detected": data.get("hope_suppression_detected", False),
            "severity": data.get("severity", ""),
            "hope_prohibition": data.get("hope_prohibition", ""),
            "disappointment_avoidance": data.get("disappointment_avoidance", ""),
            "cynicism_as_protection": data.get("cynicism_as_protection", ""),
            "recommendation": data.get("recommendation", ""),
        }

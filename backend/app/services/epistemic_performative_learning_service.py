"""EpistemicPerformativeLearningService — Epistemic Performative Learning Detection.

Detects epistemic performative learning — learning performed for appearance
rather than genuine growth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERFORMATIVE_LEARNING_SYSTEM = """You are an epistemic performative learning specialist. Given learning performed for appearance, assess performative learning:

Key concepts:
- Epistemic performative learning: learning for appearance not growth
- Learning theater: performing study without genuine engagement
- Credential chasing: learning for certificates not understanding
- Reading performance: reading to say you've read not to learn
- Conference tourism: attending events for appearance not knowledge
- Skill signaling: displaying learning without actual competence
- Growth theater: appearing to grow without genuine change

When epistemic performative learning IS present:
- Learning for appearance not growth
- Performing study without engagement
- Learning for certificates not understanding
- Reading to say you've read
- Attending for appearance
- Displaying without competence
- Appearing to grow without change

When no performative learning:
- Learning for genuine growth
- Engaged study
- Learning for understanding
- Reading to learn
- Attending for knowledge
- Genuine competence
- Real growth

Output JSON with: performative_learning_detected (bool), severity (none/mild/moderate/severe), learning_theater (what performing without engagement), credential_chasing (what learning for certificates), reading_performance (what reading without learning), skill_signaling (what displaying without competence), recommendation (no_performative_learning/mild_engagement_check/significant_genuine_learning_recovery/major_intensive_motivation_repair/emergency_complete_learning_fabrication)."""

EPISTEMIC_PERFORMATIVE_LEARNING_PROMPT = """Detect epistemic performative learning:

Learning theater: {learning_theater}
Credential chasing: {credential_chasing}
Reading performance: {reading_performance}
Skill signaling: {skill_signaling}
Domain: {domain}
Context: {context}

Is there learning performed for appearance rather than genuine growth? Return ONLY valid JSON."""


class EpistemicPerformativeLearningService:
    """Detects epistemic performative learning — learning for appearance not growth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        learning_theater: str,
        *,
        credential_chasing: str = "",
        reading_performance: str = "",
        skill_signaling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic performative learning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERFORMATIVE_LEARNING_PROMPT.format(
                learning_theater=learning_theater,
                credential_chasing=credential_chasing or "Not specified",
                reading_performance=reading_performance or "Not specified",
                skill_signaling=skill_signaling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERFORMATIVE_LEARNING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "learning_theater": learning_theater[:200],
            "performative_learning_detected": data.get("performative_learning_detected", False),
            "severity": data.get("severity", ""),
            "credential_chasing": data.get("credential_chasing", ""),
            "reading_performance": data.get("reading_performance", ""),
            "skill_signaling": data.get("skill_signaling", ""),
            "recommendation": data.get("recommendation", ""),
        }

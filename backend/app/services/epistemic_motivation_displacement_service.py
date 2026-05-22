"""EpistemicMotivationDisplacementService — Epistemic Motivation Displacement Detection.

Detects epistemic motivation displacement — displacing epistemic motivation
onto non-epistemic goals like social status or emotional comfort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOTIVATION_DISPLACEMENT_SYSTEM = """You are an epistemic motivation displacement specialist. Given displacing epistemic motivation onto non-epistemic goals, assess motivation displacement:

Key concepts:
- Epistemic motivation displacement: displacing epistemic motivation onto non-epistemic goals
- Knowledge as status: using knowledge for status not understanding
- Learning as performance: learning to perform not to know
- Inquiry as avoidance: using inquiry to avoid other responsibilities
- Understanding as control: seeking understanding for control not truth
- Curiosity as escape: using curiosity to escape rather than learn
- Research as procrastination: researching to avoid acting

When epistemic motivation displacement IS present:
- Motivation displaced onto non-epistemic goals
- Knowledge used for status
- Learning as performance
- Inquiry as avoidance
- Understanding for control
- Curiosity as escape
- Research as procrastination

When no motivation displacement:
- Motivation directed at understanding
- Knowledge valued for itself
- Learning for genuine knowing
- Inquiry for truth
- Understanding for wisdom
- Curiosity for discovery
- Research for insight

Output JSON with: motivation_displacement_detected (bool), severity (none/mild/moderate/severe), knowledge_as_status (what knowledge used for status), learning_as_performance (what learning performed rather than internalized), inquiry_as_avoidance (what inquiry avoiding), curiosity_as_escape (what curiosity escaping from), recommendation (no_motivation_displacement/mild_purpose_clarification/significant_motivation_redirection/major_intensive_purpose_recovery/emergency_complete_motivation_displacement)."""

EPISTEMIC_MOTIVATION_DISPLACEMENT_PROMPT = """Detect epistemic motivation displacement:

Knowledge as status: {knowledge_as_status}
Learning as performance: {learning_as_performance}
Inquiry as avoidance: {inquiry_as_avoidance}
Curiosity as escape: {curiosity_as_escape}
Domain: {domain}
Context: {context}

Is epistemic motivation being displaced onto non-epistemic goals? Return ONLY valid JSON."""


class EpistemicMotivationDisplacementService:
    """Detects epistemic motivation displacement — displacing motivation onto non-epistemic goals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_as_status: str,
        *,
        learning_as_performance: str = "",
        inquiry_as_avoidance: str = "",
        curiosity_as_escape: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic motivation displacement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOTIVATION_DISPLACEMENT_PROMPT.format(
                knowledge_as_status=knowledge_as_status,
                learning_as_performance=learning_as_performance or "Not specified",
                inquiry_as_avoidance=inquiry_as_avoidance or "Not specified",
                curiosity_as_escape=curiosity_as_escape or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOTIVATION_DISPLACEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_as_status": knowledge_as_status[:200],
            "motivation_displacement_detected": data.get("motivation_displacement_detected", False),
            "severity": data.get("severity", ""),
            "learning_as_performance": data.get("learning_as_performance", ""),
            "inquiry_as_avoidance": data.get("inquiry_as_avoidance", ""),
            "curiosity_as_escape": data.get("curiosity_as_escape", ""),
            "recommendation": data.get("recommendation", ""),
        }

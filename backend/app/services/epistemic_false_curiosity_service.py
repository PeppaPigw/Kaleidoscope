"""EpistemicFalseCuriosityService — Epistemic False Curiosity Detection.

Detects epistemic false curiosity — feigning curiosity without genuine
interest in answers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FALSE_CURIOSITY_SYSTEM = """You are an epistemic false curiosity specialist. Given feigning curiosity without genuine interest, assess false curiosity:

Key concepts:
- Epistemic false curiosity: feigning curiosity without genuine interest
- Performative questioning: asking questions for appearance not answers
- Rhetorical curiosity: questions designed to make a point not learn
- Social questioning: asking to appear engaged not to understand
- Curiosity theater: performing interest without follow-through
- Strategic inquiry: questions as weapons not genuine exploration
- Pseudo-engagement: appearing interested while mentally checked out

When epistemic false curiosity IS present:
- Feigning curiosity without interest
- Asking for appearance not answers
- Questions to make points not learn
- Asking to appear engaged
- Performing interest without follow-through
- Questions as weapons
- Appearing interested while checked out

When no false curiosity:
- Genuine curiosity
- Asking to learn
- Questions for understanding
- Authentic engagement
- Following through on answers
- Questions for exploration
- Genuinely interested

Output JSON with: false_curiosity_detected (bool), severity (none/mild/moderate/severe), performative_questioning (what asking for appearance), rhetorical_curiosity (what questions making points), curiosity_theater (what performing without follow-through), strategic_inquiry (what questions as weapons), recommendation (no_false_curiosity/mild_sincerity_check/significant_genuine_curiosity_building/major_intensive_engagement_work/emergency_complete_curiosity_fabrication)."""

EPISTEMIC_FALSE_CURIOSITY_PROMPT = """Detect epistemic false curiosity:

Performative questioning: {performative_questioning}
Rhetorical curiosity: {rhetorical_curiosity}
Curiosity theater: {curiosity_theater}
Strategic inquiry: {strategic_inquiry}
Domain: {domain}
Context: {context}

Is there feigning curiosity without genuine interest in answers? Return ONLY valid JSON."""


class EpistemicFalseCuriosityService:
    """Detects epistemic false curiosity — feigning curiosity without genuine interest."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        performative_questioning: str,
        *,
        rhetorical_curiosity: str = "",
        curiosity_theater: str = "",
        strategic_inquiry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false curiosity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FALSE_CURIOSITY_PROMPT.format(
                performative_questioning=performative_questioning,
                rhetorical_curiosity=rhetorical_curiosity or "Not specified",
                curiosity_theater=curiosity_theater or "Not specified",
                strategic_inquiry=strategic_inquiry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FALSE_CURIOSITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "performative_questioning": performative_questioning[:200],
            "false_curiosity_detected": data.get("false_curiosity_detected", False),
            "severity": data.get("severity", ""),
            "rhetorical_curiosity": data.get("rhetorical_curiosity", ""),
            "curiosity_theater": data.get("curiosity_theater", ""),
            "strategic_inquiry": data.get("strategic_inquiry", ""),
            "recommendation": data.get("recommendation", ""),
        }

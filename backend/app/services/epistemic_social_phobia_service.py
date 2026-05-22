"""EpistemicSocialPhobiaService — Epistemic Social Phobia Detection.

Detects epistemic social phobia — intense fear of intellectual judgment
and evaluation by others in intellectual settings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_PHOBIA_SYSTEM = """You are an epistemic social phobia specialist. Given fear of intellectual judgment, assess social phobia:

Key concepts:
- Epistemic social phobia: intense fear of intellectual judgment
- Performance anxiety: terror of intellectual evaluation
- Scrutiny fear: believing others are judging intellectual output
- Humiliation dread: expecting intellectual embarrassment
- Avoidance: refusing to share ideas publicly
- Safety behaviors: minimizing intellectual exposure
- Anticipatory distress: anxiety before intellectual interactions

When epistemic social phobia IS present:
- Intense fear of judgment
- Terror of evaluation
- Believing others judging
- Expecting embarrassment
- Refusing to share publicly
- Minimizing exposure
- Anxiety before interactions

When no social phobia:
- Comfortable with judgment
- Calm during evaluation
- Realistic about others
- Confident in sharing
- Willing to share publicly
- Normal exposure levels
- Calm before interactions

Output JSON with: social_phobia_detected (bool), severity (none/mild/moderate/severe), judgment_fear (what evaluation anxiety), performance_anxiety (what terror), avoidance_pattern (what refusal), safety_behaviors (what minimizing), recommendation (no_social_phobia/mild_gradual_exposure/significant_cbt/major_intensive_therapy/emergency_complete_avoidance)."""

EPISTEMIC_SOCIAL_PHOBIA_PROMPT = """Detect epistemic social phobia:

Judgment fear: {judgment_fear}
Performance anxiety: {performance_anxiety}
Avoidance pattern: {avoidance_pattern}
Safety behaviors: {safety_behaviors}
Domain: {domain}
Context: {context}

Is there intense fear of intellectual judgment and evaluation by others? Return ONLY valid JSON."""


class EpistemicSocialPhobiaService:
    """Detects epistemic social phobia — fear of intellectual judgment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment_fear: str,
        *,
        performance_anxiety: str = "",
        avoidance_pattern: str = "",
        safety_behaviors: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social phobia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_PHOBIA_PROMPT.format(
                judgment_fear=judgment_fear,
                performance_anxiety=performance_anxiety or "Not specified",
                avoidance_pattern=avoidance_pattern or "Not specified",
                safety_behaviors=safety_behaviors or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_PHOBIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment_fear": judgment_fear[:200],
            "social_phobia_detected": data.get("social_phobia_detected", False),
            "severity": data.get("severity", ""),
            "performance_anxiety": data.get("performance_anxiety", ""),
            "avoidance_pattern": data.get("avoidance_pattern", ""),
            "safety_behaviors": data.get("safety_behaviors", ""),
            "recommendation": data.get("recommendation", ""),
        }

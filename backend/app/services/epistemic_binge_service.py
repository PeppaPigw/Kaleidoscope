"""EpistemicBingeService — Epistemic Binge Eating Detection.

Detects epistemic binge eating — compulsive overconsumption of information
without retention or integration, driven by emotional needs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BINGE_SYSTEM = """You are an epistemic binge eating specialist. Given compulsive information overconsumption, assess binge patterns:

Key concepts:
- Epistemic binge: compulsive overconsumption of information
- Emotional eating: consuming information to soothe emotions
- Loss of control: unable to stop consuming
- No retention: information passes through without integration
- Distress: guilt and shame after binge episodes
- Trigger-driven: emotional states precipitate binges
- Numbing: using information consumption to avoid feelings

When epistemic binge IS present:
- Compulsive overconsumption
- Consuming to soothe emotions
- Unable to stop
- No retention or integration
- Guilt after episodes
- Emotional triggers
- Using consumption to avoid feelings

When no binge:
- Purposeful consumption
- Learning for growth
- Able to stop when satisfied
- Good retention
- No guilt about learning
- Internally motivated
- Emotionally present while learning

Output JSON with: binge_detected (bool), severity (none/mild/moderate/severe), consumption_pattern (what overconsumption), emotional_trigger (what drives binge), retention_level (what integration), distress_after (what guilt), recommendation (no_binge/mild_mindful_consumption/significant_structured_program/major_intensive_therapy/emergency_complete_compulsion)."""

EPISTEMIC_BINGE_PROMPT = """Detect epistemic binge eating:

Consumption pattern: {consumption_pattern}
Emotional trigger: {emotional_trigger}
Retention level: {retention_level}
Distress after: {distress_after}
Domain: {domain}
Context: {context}

Is there compulsive overconsumption of information without retention? Return ONLY valid JSON."""


class EpistemicBingeService:
    """Detects epistemic binge eating — compulsive information overconsumption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consumption_pattern: str,
        *,
        emotional_trigger: str = "",
        retention_level: str = "",
        distress_after: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic binge eating."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BINGE_PROMPT.format(
                consumption_pattern=consumption_pattern,
                emotional_trigger=emotional_trigger or "Not specified",
                retention_level=retention_level or "Not specified",
                distress_after=distress_after or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BINGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consumption_pattern": consumption_pattern[:200],
            "binge_detected": data.get("binge_detected", False),
            "severity": data.get("severity", ""),
            "emotional_trigger": data.get("emotional_trigger", ""),
            "retention_level": data.get("retention_level", ""),
            "distress_after": data.get("distress_after", ""),
            "recommendation": data.get("recommendation", ""),
        }

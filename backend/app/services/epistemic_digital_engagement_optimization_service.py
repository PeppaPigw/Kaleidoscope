"""EpistemicDigitalEngagementOptimizationService — Epistemic Engagement Optimization Detection.

Detects epistemic digital engagement optimization — engagement optimization
distorting information salience by promoting emotionally engaging over accurate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIGITAL_ENGAGEMENT_OPTIMIZATION_SYSTEM = """You are an epistemic digital engagement optimization specialist. Given engagement optimization, assess salience distortion:

Key concepts:
- Epistemic engagement optimization: engagement metrics distorting salience
- Outrage amplification: outrage-inducing content promoted for engagement
- Clickbait epistemics: misleading framing for clicks
- Emotional over accurate: emotional content promoted over accurate
- Attention hijacking: attention captured by engaging not important content
- Dopamine-driven information: information consumption driven by dopamine
- Accuracy-engagement tradeoff: accuracy sacrificed for engagement

When epistemic engagement optimization IS present:
- Engagement distorting salience
- Outrage amplified
- Clickbait framing
- Emotional over accurate
- Attention hijacked
- Dopamine driving consumption
- Accuracy sacrificed

When no engagement optimization distortion:
- Salience based on importance
- Outrage not amplified
- Framing honest
- Accuracy prioritized
- Attention directed appropriately
- Consumption deliberate
- Engagement aligned with quality

Output JSON with: engagement_optimization_detected (bool), severity (none/mild/moderate/severe), outrage_amplification (what outrage amplified), clickbait_epistemics (what clickbait framing), emotional_over_accurate (what emotional over accurate), attention_hijacking (what attention hijacked), recommendation (no_engagement_optimization/mild_salience_awareness/significant_engagement_resistance/major_intensive_attention_reform/emergency_complete_engagement_optimization)."""

EPISTEMIC_DIGITAL_ENGAGEMENT_OPTIMIZATION_PROMPT = """Detect epistemic digital engagement optimization:

Outrage amplification: {outrage_amplification}
Clickbait epistemics: {clickbait_epistemics}
Emotional over accurate: {emotional_over_accurate}
Attention hijacking: {attention_hijacking}
Domain: {domain}
Context: {context}

Is engagement optimization distorting information salience? Return ONLY valid JSON."""


class EpistemicDigitalEngagementOptimizationService:
    """Detects epistemic engagement optimization — salience distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outrage_amplification: str,
        *,
        clickbait_epistemics: str = "",
        emotional_over_accurate: str = "",
        attention_hijacking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic digital engagement optimization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIGITAL_ENGAGEMENT_OPTIMIZATION_PROMPT.format(
                outrage_amplification=outrage_amplification,
                clickbait_epistemics=clickbait_epistemics or "Not specified",
                emotional_over_accurate=emotional_over_accurate or "Not specified",
                attention_hijacking=attention_hijacking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIGITAL_ENGAGEMENT_OPTIMIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outrage_amplification": outrage_amplification[:200],
            "engagement_optimization_detected": data.get("engagement_optimization_detected", False),
            "severity": data.get("severity", ""),
            "clickbait_epistemics": data.get("clickbait_epistemics", ""),
            "emotional_over_accurate": data.get("emotional_over_accurate", ""),
            "attention_hijacking": data.get("attention_hijacking", ""),
            "recommendation": data.get("recommendation", ""),
        }

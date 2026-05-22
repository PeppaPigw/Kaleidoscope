"""EpistemicDigitalPlatformIncentiveService — Epistemic Digital Platform Incentive Detection.

Detects epistemic digital platform incentive — platform business models
distorting information ecosystem by prioritizing engagement over accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIGITAL_PLATFORM_INCENTIVE_SYSTEM = """You are an epistemic digital platform incentive specialist. Given platform incentive distortion, assess ecosystem effects:

Key concepts:
- Epistemic platform incentive: platform business models distorting information
- Attention economy: platforms monetizing attention regardless of content quality
- Algorithmic amplification: algorithms amplifying divisive/engaging content
- Creator incentive distortion: creator incentives misaligned with accuracy
- Moderation asymmetry: moderation favoring engagement over accuracy
- Data exploitation: user data used to optimize manipulation
- Platform lock-in: lock-in preventing migration to better information sources

When epistemic platform incentive IS present:
- Platform models distorting information
- Attention monetized regardless of quality
- Algorithms amplifying divisive content
- Creator incentives misaligned
- Moderation favoring engagement
- Data exploited for manipulation
- Lock-in preventing alternatives

When no platform incentive distortion:
- Platform models aligned with quality
- Quality content rewarded
- Algorithms promoting accuracy
- Creator incentives aligned
- Moderation prioritizing accuracy
- Data used responsibly
- Users free to migrate

Output JSON with: platform_incentive_detected (bool), severity (none/mild/moderate/severe), attention_economy_distortion (what attention economy distorting), algorithmic_amplification (what algorithms amplifying), creator_incentive_distortion (what creator incentives distorted), moderation_asymmetry (what moderation asymmetry), recommendation (no_platform_incentive/mild_platform_awareness/significant_platform_resistance/major_intensive_platform_reform/emergency_complete_platform_incentive)."""

EPISTEMIC_DIGITAL_PLATFORM_INCENTIVE_PROMPT = """Detect epistemic digital platform incentive distortion:

Attention economy distortion: {attention_economy_distortion}
Algorithmic amplification: {algorithmic_amplification}
Creator incentive distortion: {creator_incentive_distortion}
Moderation asymmetry: {moderation_asymmetry}
Domain: {domain}
Context: {context}

Are platform business models distorting the information ecosystem? Return ONLY valid JSON."""


class EpistemicDigitalPlatformIncentiveService:
    """Detects epistemic platform incentive — ecosystem distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attention_economy_distortion: str,
        *,
        algorithmic_amplification: str = "",
        creator_incentive_distortion: str = "",
        moderation_asymmetry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic digital platform incentive."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIGITAL_PLATFORM_INCENTIVE_PROMPT.format(
                attention_economy_distortion=attention_economy_distortion,
                algorithmic_amplification=algorithmic_amplification or "Not specified",
                creator_incentive_distortion=creator_incentive_distortion or "Not specified",
                moderation_asymmetry=moderation_asymmetry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIGITAL_PLATFORM_INCENTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attention_economy_distortion": attention_economy_distortion[:200],
            "platform_incentive_detected": data.get("platform_incentive_detected", False),
            "severity": data.get("severity", ""),
            "algorithmic_amplification": data.get("algorithmic_amplification", ""),
            "creator_incentive_distortion": data.get("creator_incentive_distortion", ""),
            "moderation_asymmetry": data.get("moderation_asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }

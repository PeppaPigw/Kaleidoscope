"""EpistemicGrowthAvoidanceService — Epistemic Growth Avoidance Detection.

Detects epistemic growth avoidance — avoiding intellectual growth
to maintain comfort and familiar patterns of thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROWTH_AVOIDANCE_SYSTEM = """You are an epistemic growth avoidance specialist. Given avoiding intellectual growth, assess growth avoidance:

Key concepts:
- Epistemic growth avoidance: avoiding growth to maintain comfort
- Comfort zone clinging: staying in intellectual comfort zone
- Challenge avoidance: avoiding intellectual challenges
- Stagnation preference: preferring stagnation over growth discomfort
- Learning resistance: resisting new learning opportunities
- Complexity avoidance: avoiding complex topics that would require growth
- Familiar pattern addiction: addicted to familiar thinking patterns

When epistemic growth avoidance IS present:
- Avoiding growth for comfort
- Staying in comfort zone
- Avoiding challenges
- Preferring stagnation
- Resisting learning
- Avoiding complexity
- Addicted to familiar patterns

When no growth avoidance:
- Embracing growth
- Leaving comfort zone
- Seeking challenges
- Preferring growth
- Welcoming learning
- Engaging complexity
- Open to new patterns

Output JSON with: growth_avoidance_detected (bool), severity (none/mild/moderate/severe), comfort_zone_clinging (what comfort zone clinging to), challenge_avoidance (what challenges avoiding), stagnation_preference (what preferring stagnation about), learning_resistance (what resisting learning about), recommendation (no_growth_avoidance/mild_stretch_practice/significant_challenge_seeking/major_intensive_growth_commitment/emergency_complete_growth_refusal)."""

EPISTEMIC_GROWTH_AVOIDANCE_PROMPT = """Detect epistemic growth avoidance:

Comfort zone clinging: {comfort_zone_clinging}
Challenge avoidance: {challenge_avoidance}
Stagnation preference: {stagnation_preference}
Learning resistance: {learning_resistance}
Domain: {domain}
Context: {context}

Is there avoiding intellectual growth to maintain comfort? Return ONLY valid JSON."""


class EpistemicGrowthAvoidanceService:
    """Detects epistemic growth avoidance — avoiding growth for comfort."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comfort_zone_clinging: str,
        *,
        challenge_avoidance: str = "",
        stagnation_preference: str = "",
        learning_resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic growth avoidance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROWTH_AVOIDANCE_PROMPT.format(
                comfort_zone_clinging=comfort_zone_clinging,
                challenge_avoidance=challenge_avoidance or "Not specified",
                stagnation_preference=stagnation_preference or "Not specified",
                learning_resistance=learning_resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROWTH_AVOIDANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comfort_zone_clinging": comfort_zone_clinging[:200],
            "growth_avoidance_detected": data.get("growth_avoidance_detected", False),
            "severity": data.get("severity", ""),
            "challenge_avoidance": data.get("challenge_avoidance", ""),
            "stagnation_preference": data.get("stagnation_preference", ""),
            "learning_resistance": data.get("learning_resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }

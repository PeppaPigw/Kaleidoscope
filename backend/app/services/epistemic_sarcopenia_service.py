"""EpistemicSarcopeniaService — Epistemic Sarcopenia Detection.

Detects epistemic sarcopenia — age-related loss of intellectual muscle mass
and strength, reducing capacity for cognitive work.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SARCOPENIA_SYSTEM = """You are an epistemic sarcopenia specialist. Given intellectual muscle loss, assess sarcopenia:

Key concepts:
- Epistemic sarcopenia: loss of intellectual muscle mass and strength
- Muscle mass: quantity of intellectual processing capacity
- Grip strength: ability to hold and manipulate ideas
- Gait speed: rate of intellectual processing
- Anabolic resistance: inability to build new capacity
- Catabolic state: breaking down faster than building
- Resistance training: exercises to maintain capacity

When epistemic sarcopenia IS present:
- Loss of intellectual processing capacity
- Reduced ability to hold ideas
- Slowed processing rate
- Cannot build new capacity
- Breaking down faster than building
- Exercises not maintaining capacity
- Progressive weakness

When no sarcopenia:
- Adequate processing capacity
- Strong idea manipulation
- Normal processing speed
- Building capacity normally
- Balanced build/breakdown
- Exercises effective
- Maintained strength

Output JSON with: sarcopenia_detected (bool), severity (none/mild/moderate/severe), muscle_mass (what capacity level), grip_strength (what manipulation ability), gait_speed (what processing rate), anabolic_status (what building capacity), recommendation (no_sarcopenia/mild_pre_sarcopenia/significant_sarcopenia/major_severe_sarcopenia/advanced_sarcopenic_disability)."""

EPISTEMIC_SARCOPENIA_PROMPT = """Detect epistemic sarcopenia:

Muscle mass: {muscle_mass}
Grip strength: {grip_strength}
Gait speed: {gait_speed}
Anabolic status: {anabolic_status}
Domain: {domain}
Context: {context}

Is there age-related loss of intellectual muscle mass and strength? Return ONLY valid JSON."""


class EpistemicSarcopeniaService:
    """Detects epistemic sarcopenia — loss of intellectual muscle mass and strength."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        muscle_mass: str,
        *,
        grip_strength: str = "",
        gait_speed: str = "",
        anabolic_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sarcopenia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SARCOPENIA_PROMPT.format(
                muscle_mass=muscle_mass,
                grip_strength=grip_strength or "Not specified",
                gait_speed=gait_speed or "Not specified",
                anabolic_status=anabolic_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SARCOPENIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "muscle_mass": muscle_mass[:200],
            "sarcopenia_detected": data.get("sarcopenia_detected", False),
            "severity": data.get("severity", ""),
            "grip_strength": data.get("grip_strength", ""),
            "gait_speed": data.get("gait_speed", ""),
            "anabolic_status": data.get("anabolic_status", ""),
            "recommendation": data.get("recommendation", ""),
        }

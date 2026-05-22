"""EpistemicSpoilingAttackService — Epistemic Spoiling Attack Detection.

Detects epistemic spoiling attacks — attacking what one envies to destroy
its value so it can no longer be envied.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPOILING_ATTACK_SYSTEM = """You are an epistemic spoiling attack specialist. Given attacks on envied objects, assess spoiling:

Key concepts:
- Epistemic spoiling attack: destroying value of envied thing
- Devaluation: making envied achievement seem worthless
- Contamination: adding negativity to spoil the good
- Critique as weapon: using criticism to destroy not improve
- Sour grapes: declaring envied thing not worth having
- Poisoning: making others see envied thing negatively
- Triumph in destruction: satisfaction when value destroyed

When epistemic spoiling attack IS present:
- Destroying value of envied
- Making achievement worthless
- Adding negativity to spoil
- Criticism to destroy
- Declaring not worth having
- Making others see negatively
- Satisfaction in destruction

When no spoiling attack:
- Preserving value
- Acknowledging achievement
- Adding constructively
- Criticism to improve
- Recognizing worth
- Fair representation
- No destructive satisfaction

Output JSON with: spoiling_attack_detected (bool), severity (none/mild/moderate/severe), devaluation_target (what making worthless), contamination_method (what spoiling), critique_as_weapon (what destroying with), triumph_pattern (what satisfaction in), recommendation (no_spoiling_attack/mild_envy_awareness/significant_gratitude_practice/major_intensive_envy_therapy/emergency_active_destruction)."""

EPISTEMIC_SPOILING_ATTACK_PROMPT = """Detect epistemic spoiling attack:

Devaluation target: {devaluation_target}
Contamination method: {contamination_method}
Critique as weapon: {critique_as_weapon}
Triumph pattern: {triumph_pattern}
Domain: {domain}
Context: {context}

Is there attacking what one envies to destroy its value? Return ONLY valid JSON."""


class EpistemicSpoilingAttackService:
    """Detects epistemic spoiling attacks — destroying value of envied things."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        devaluation_target: str,
        *,
        contamination_method: str = "",
        critique_as_weapon: str = "",
        triumph_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic spoiling attack."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPOILING_ATTACK_PROMPT.format(
                devaluation_target=devaluation_target,
                contamination_method=contamination_method or "Not specified",
                critique_as_weapon=critique_as_weapon or "Not specified",
                triumph_pattern=triumph_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPOILING_ATTACK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "devaluation_target": devaluation_target[:200],
            "spoiling_attack_detected": data.get("spoiling_attack_detected", False),
            "severity": data.get("severity", ""),
            "contamination_method": data.get("contamination_method", ""),
            "critique_as_weapon": data.get("critique_as_weapon", ""),
            "triumph_pattern": data.get("triumph_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

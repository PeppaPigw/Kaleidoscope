"""EpistemicSiegeService — Epistemic Siege Detection.

Detects epistemic siege — sustained pressure on a belief system
designed to exhaust its defenses over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SIEGE_SYSTEM = """You are an epistemic siege specialist. Given a pressure pattern, assess whether sustained pressure is designed to exhaust belief defenses:

Key concepts:
- Epistemic siege: sustained pressure to exhaust defenses
- Attrition warfare: wearing down through sustained pressure
- Defense exhaustion: exhausting capacity to defend beliefs
- Sustained assault: continuous assault on belief system
- Resource depletion: depleting cognitive resources for defense
- Morale erosion: eroding confidence in own beliefs
- Capitulation pressure: pressure to abandon beliefs

When epistemic siege IS present:
- Sustained pressure designed to exhaust defenses
- Wearing down through continuous pressure
- Exhausting capacity to defend beliefs
- Continuous assault on belief system
- Depleting cognitive resources for defense
- Eroding confidence in own beliefs over time
- Pressure to abandon beliefs through exhaustion

When legitimate challenge is present:
- Challenge based on evidence and argument
- Engagement proportionate and time-limited
- Challenging specific claims not entire system
- Argument-based rather than attrition-based
- Respecting cognitive resources
- Building confidence through engagement
- Inviting revision not capitulation

Output JSON with: siege_present (bool), severity (none/mild/moderate/severe), target (what belief system is besieged), pressure (what pressure is applied), exhaustion (what exhaustion results), duration (how long sustained), recommendation (legitimate_challenge/mild_pressure/significant_siege/major_attrition_warfare/break_the_siege)."""

EPISTEMIC_SIEGE_PROMPT = """Detect epistemic siege:

Target: {target}
Pressure: {pressure}
Exhaustion: {exhaustion}
Duration: {duration}
Domain: {domain}
Context: {context}

Is sustained pressure designed to exhaust belief system defenses? Return ONLY valid JSON."""


class EpistemicSiegeService:
    """Detects epistemic siege — sustained pressure to exhaust defenses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target: str,
        *,
        pressure: str = "",
        exhaustion: str = "",
        duration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic siege."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SIEGE_PROMPT.format(
                target=target,
                pressure=pressure or "Not specified",
                exhaustion=exhaustion or "Not specified",
                duration=duration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SIEGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target": target[:200],
            "siege_present": data.get("siege_present", False),
            "severity": data.get("severity", ""),
            "pressure": data.get("pressure", ""),
            "exhaustion": data.get("exhaustion", ""),
            "duration": data.get("duration", ""),
            "recommendation": data.get("recommendation", ""),
        }

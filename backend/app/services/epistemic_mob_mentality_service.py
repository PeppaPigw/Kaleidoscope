"""EpistemicMobMentalityService — Epistemic Mob Mentality Detection.

Detects epistemic mob mentality — loss of individual intellectual judgment
in crowd situations where emotional intensity overrides rational thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MOB_MENTALITY_SYSTEM = """You are an epistemic mob mentality specialist. Given loss of individual judgment in crowds, assess mob mentality:

Key concepts:
- Epistemic mob mentality: loss of individual judgment in crowd
- Deindividuation: losing sense of individual intellectual identity
- Emotional override: feelings replacing thinking
- Anonymity effect: reduced accountability in group
- Escalation: each action enables more extreme next
- Contagion: behavior spreading without reflection
- Regret: later recognizing actions were unlike self

When epistemic mob mentality IS present:
- Loss of individual judgment
- Losing intellectual identity
- Feelings replacing thinking
- Reduced accountability
- Escalating extremity
- Behavior spreading unreflectively
- Later regret

When no mob mentality:
- Individual judgment intact
- Intellectual identity maintained
- Thinking guiding feelings
- Full accountability
- Proportionate response
- Reflective behavior
- Consistent with values

Output JSON with: mob_mentality_detected (bool), severity (none/mild/moderate/severe), deindividuation_level (what losing identity), emotional_override (what replacing thinking), escalation_pattern (what enabling extreme), contagion_speed (what spreading), recommendation (no_mob_mentality/mild_individuation_practice/significant_group_intervention/major_intensive_separation/emergency_dangerous_escalation)."""

EPISTEMIC_MOB_MENTALITY_PROMPT = """Detect epistemic mob mentality:

Deindividuation level: {deindividuation_level}
Emotional override: {emotional_override}
Escalation pattern: {escalation_pattern}
Contagion speed: {contagion_speed}
Domain: {domain}
Context: {context}

Is there loss of individual intellectual judgment in crowd situations? Return ONLY valid JSON."""


class EpistemicMobMentalityService:
    """Detects epistemic mob mentality — loss of individual judgment in crowds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deindividuation_level: str,
        *,
        emotional_override: str = "",
        escalation_pattern: str = "",
        contagion_speed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mob mentality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MOB_MENTALITY_PROMPT.format(
                deindividuation_level=deindividuation_level,
                emotional_override=emotional_override or "Not specified",
                escalation_pattern=escalation_pattern or "Not specified",
                contagion_speed=contagion_speed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MOB_MENTALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deindividuation_level": deindividuation_level[:200],
            "mob_mentality_detected": data.get("mob_mentality_detected", False),
            "severity": data.get("severity", ""),
            "emotional_override": data.get("emotional_override", ""),
            "escalation_pattern": data.get("escalation_pattern", ""),
            "contagion_speed": data.get("contagion_speed", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""ReactanceService — Psychological Reactance Detection.

Detects psychological reactance — the motivational state that
arises when freedoms are threatened or eliminated, leading to
behavior opposite to what's being urged. Brehm (1966). Tell
someone they can't do something and they want to do it more.
Mandate something and they resist. The "don't push me" effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REACTANCE_SYSTEM = """You are a psychological reactance specialist. Given a persuasion attempt or restriction, assess whether reactance is causing oppositional behavior:

Key concepts (Brehm, 1966):
- Reactance: motivational arousal when freedom is threatened
- Boomerang effect: persuasion attempts backfire, producing opposite behavior
- Forbidden fruit: restrictions increase desire for the restricted thing
- Autonomy threat: perceived loss of choice triggers resistance
- Magnitude factors: importance of freedom, number of freedoms threatened, strength of threat
- Restoration behavior: acting to reassert the threatened freedom

When reactance IS present:
- Doing the opposite of what's being urged specifically because it's being urged
- Resistance to mandates that would otherwise be accepted voluntarily
- "Don't tell me what to do" response to reasonable requests
- Increased desire for something specifically because it's forbidden
- Rejecting good advice because it feels like a command
- Contrarian behavior driven by autonomy threat rather than genuine disagreement

When opposition IS genuine:
- The person has substantive reasons for disagreeing
- The opposition existed before the persuasion attempt
- The restriction is genuinely unreasonable or harmful
- The person would oppose this regardless of how it was communicated
- The resistance is proportional to the actual imposition

Output JSON with: reactance_present (bool), severity (none/mild/moderate/severe), freedom_threatened (what freedom is being restricted), threat_source (who/what is threatening the freedom), threat_type (mandate/prohibition/persuasion/social_pressure), opposition_behavior (what oppositional behavior results), genuine_disagreement (bool — would they oppose this anyway?), autonomy_importance (how important is this freedom to the person?), communication_style (how was the restriction communicated?), proportionality (is the reaction proportional to the threat?), boomerang_effect (bool — is the persuasion producing the opposite effect?), restoration_attempt (how is the person trying to reassert freedom?), better_approach (how to achieve the goal without triggering reactance), recommendation (opposition_genuine/mild_reactance/significant_reactance/major_boomerang/reframe_as_choice)."""

REACTANCE_PROMPT = """Detect psychological reactance:

Situation: {situation}
Restriction/persuasion: {restriction}
Response: {response}
Communication style: {style}
Domain: {domain}
Context: {context}

Is reactance causing oppositional behavior? Return ONLY valid JSON."""


class ReactanceService:
    """Detects psychological reactance — oppositional response to freedom threats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        restriction: str = "",
        response: str = "",
        style: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect psychological reactance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REACTANCE_PROMPT.format(
                situation=situation,
                restriction=restriction or "Not specified",
                response=response or "Not specified",
                style=style or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REACTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "reactance_present": data.get("reactance_present", False),
            "severity": data.get("severity", ""),
            "freedom_threatened": data.get("freedom_threatened", ""),
            "threat_source": data.get("threat_source", ""),
            "threat_type": data.get("threat_type", ""),
            "opposition_behavior": data.get("opposition_behavior", ""),
            "genuine_disagreement": data.get("genuine_disagreement", False),
            "autonomy_importance": data.get("autonomy_importance", ""),
            "communication_style": data.get("communication_style", ""),
            "proportionality": data.get("proportionality", ""),
            "boomerang_effect": data.get("boomerang_effect", False),
            "restoration_attempt": data.get("restoration_attempt", ""),
            "better_approach": data.get("better_approach", ""),
            "recommendation": data.get("recommendation", ""),
        }

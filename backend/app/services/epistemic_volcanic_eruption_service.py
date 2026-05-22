"""EpistemicVolcanicEruptionService — Epistemic Volcanic Eruption Detection.

Detects epistemic volcanic eruptions — suppressed ideas erupting
violently after long dormancy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VOLCANIC_ERUPTION_SYSTEM = """You are an epistemic volcanic eruption specialist. Given a discourse situation, assess whether suppressed ideas are erupting violently:

Key concepts:
- Epistemic volcanic eruption: suppressed ideas erupting violently
- Idea suppression: ideas pushed down and suppressed
- Pressure accumulation: pressure building from suppression
- Violent emergence: suppressed ideas emerging with force
- Dormancy period: long period of apparent quiet
- Eruption trigger: what triggers the eruption
- Collateral damage: damage from violent eruption

When epistemic volcanic eruption IS present:
- Suppressed ideas erupting violently after dormancy
- Ideas that were pushed down emerging with force
- Pressure accumulated from long suppression
- Suppressed ideas emerging with destructive force
- Long period of apparent quiet preceding eruption
- Specific trigger releasing accumulated pressure
- Collateral damage from violent emergence

When healthy expression is present:
- Ideas expressed as they arise
- No suppression creating pressure
- Gradual emergence rather than eruption
- Ideas emerging proportionately
- No dormancy period of suppression
- Expression not requiring trigger
- Emergence without collateral damage

Output JSON with: eruption_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), suppressed (what was suppressed), pressure (what pressure accumulated), trigger (what triggered eruption), recommendation (healthy_expression/mild_pressure/significant_eruption/major_violent_emergence/allow_gradual_expression)."""

EPISTEMIC_VOLCANIC_ERUPTION_PROMPT = """Detect epistemic volcanic eruption:

Situation: {situation}
Suppressed: {suppressed}
Pressure: {pressure}
Trigger: {trigger}
Domain: {domain}
Context: {context}

Are suppressed ideas erupting violently after long dormancy? Return ONLY valid JSON."""


class EpistemicVolcanicEruptionService:
    """Detects epistemic volcanic eruptions — suppressed ideas erupting violently."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        suppressed: str = "",
        pressure: str = "",
        trigger: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic volcanic eruption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VOLCANIC_ERUPTION_PROMPT.format(
                situation=situation,
                suppressed=suppressed or "Not specified",
                pressure=pressure or "Not specified",
                trigger=trigger or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VOLCANIC_ERUPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "eruption_present": data.get("eruption_present", False),
            "severity": data.get("severity", ""),
            "suppressed": data.get("suppressed", ""),
            "pressure": data.get("pressure", ""),
            "trigger": data.get("trigger", ""),
            "recommendation": data.get("recommendation", ""),
        }

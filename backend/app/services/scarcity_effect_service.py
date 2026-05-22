"""ScarcityEffectService — Scarcity Effect Detection.

Detects scarcity effect — tendency to place higher value on
things that are scarce or becoming scarce. Cialdini (2001),
Worchel, Lee & Adewole (1975). "Limited time offer!"
"Only 3 left!" Scarcity increases perceived value regardless
of actual utility. Loss of availability feels worse than
never having had it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCARCITY_EFFECT_SYSTEM = """You are a scarcity effect specialist. Given a valuation or decision, assess whether perceived scarcity is inflating value beyond actual utility:

Key concepts (Cialdini, 2001; Worchel et al., 1975):
- Scarcity effect: scarce items valued more highly
- Commodity theory: unavailable items gain value
- Reactance: restricted freedom increases desire
- Loss framing: scarcity framed as potential loss
- Artificial scarcity: manufactured limitations
- Time pressure: deadlines creating urgency
- Social proof interaction: "others want it too"
- Newly scarce > always scarce: loss of availability is worse

When scarcity effect IS present:
- Valuing something more because it's "limited edition"
- Urgency from "only X left" or "offer expires soon"
- Wanting something more after learning it's unavailable
- "I need to act now or I'll miss out" (FOMO)
- Paying premium for scarcity rather than quality
- Artificial deadlines creating false urgency
- Collecting things primarily because they're rare

When the scarcity IS genuinely relevant:
- Scarcity reflects genuine supply constraints
- The item's value is genuinely tied to rarity
- Time pressure reflects real deadlines
- The person would value it equally if abundant
- Scarcity signals genuine quality (limited production)

Output JSON with: scarcity_effect_present (bool), severity (none/mild/moderate/severe), situation (what decision is being made), scarcity_signal (what scarcity cue is present), actual_utility (what is the actual utility), value_inflation (how much is value inflated by scarcity), artificial (is the scarcity manufactured), urgency (is false urgency being created), recommendation (scarcity_relevant/mild_inflation/significant_scarcity_premium/major_scarcity_manipulation/evaluate_utility_independently)."""

SCARCITY_EFFECT_PROMPT = """Detect scarcity effect:

Situation: {situation}
Scarcity signal: {signal}
Actual value: {value}
Urgency: {urgency}
Domain: {domain}
Context: {context}

Is perceived scarcity inflating value beyond actual utility? Return ONLY valid JSON."""


class ScarcityEffectService:
    """Detects scarcity effect — perceived scarcity inflating value."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        signal: str = "",
        value: str = "",
        urgency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scarcity effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCARCITY_EFFECT_PROMPT.format(
                situation=situation,
                signal=signal or "Not specified",
                value=value or "Not specified",
                urgency=urgency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCARCITY_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "scarcity_effect_present": data.get("scarcity_effect_present", False),
            "severity": data.get("severity", ""),
            "scarcity_signal": data.get("scarcity_signal", ""),
            "actual_utility": data.get("actual_utility", ""),
            "value_inflation": data.get("value_inflation", ""),
            "artificial": data.get("artificial", ""),
            "urgency": data.get("urgency", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""IkeaEffectService — IKEA Effect Detection.

Detects the IKEA effect — overvaluing things you've built or
created yourself, regardless of objective quality. Norton,
Mochon & Ariely (2012). People value their own creations
disproportionately. The amateur furniture you assembled feels
more valuable than the professional piece you bought. Related
to effort justification and endowment effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IKEA_SYSTEM = """You are an IKEA effect specialist. Given a valuation of self-created work, assess whether the creator is overvaluing it due to personal labor investment:

Key concepts (Norton, Mochon & Ariely, 2012):
- IKEA effect: overvaluing things you built yourself
- Labor = love: effort invested creates disproportionate attachment
- Effort justification overlap: "I worked hard on this, so it must be good"
- Endowment effect overlap: ownership increases perceived value
- Not-invented-here overlap: but IKEA effect is about creation, not just origin
- Completion requirement: the effect is strongest for successfully completed projects

When the IKEA effect IS present:
- Overvaluing own work relative to objectively superior alternatives
- Resistance to replacing self-built solutions with better ones
- "But I built this" as a reason to keep inferior work
- Inability to objectively assess quality of own creations
- Emotional attachment to effort rather than outcome
- Defending mediocre work because of personal investment

When self-valuation IS appropriate:
- The self-built solution genuinely meets needs better (customization)
- The quality is objectively comparable to alternatives
- The valuation accounts for maintenance costs and limitations
- The person can articulate specific advantages beyond "I made it"
- Switching costs genuinely outweigh the quality difference

Output JSON with: ikea_effect_present (bool), severity (none/mild/moderate/severe), creation (what was built/created), creator_valuation (how the creator values it), objective_valuation (how it compares objectively), effort_invested (how much labor went in), quality_gap (difference between self-assessment and objective quality), alternatives_available (what better options exist), switching_cost (genuine cost of replacing it), emotional_attachment (how attached is the creator?), completion_status (was the project completed?), customization_value (does self-building add genuine customization?), sunk_cost_interaction (bool — is sunk cost amplifying the effect?), recommendation (valuation_fair/mild_ikea_effect/significant_overvaluation/major_ikea_effect/evaluate_objectively)."""

IKEA_PROMPT = """Detect IKEA effect:

Creation: {creation}
Creator's assessment: {assessment}
Alternatives: {alternatives}
Effort invested: {effort}
Domain: {domain}
Context: {context}

Is the creator overvaluing their work due to personal labor investment? Return ONLY valid JSON."""


class IkeaEffectService:
    """Detects IKEA effect — overvaluing self-created work."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        creation: str,
        *,
        assessment: str = "",
        alternatives: str = "",
        effort: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect IKEA effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IKEA_PROMPT.format(
                creation=creation,
                assessment=assessment or "Not specified",
                alternatives=alternatives or "Not specified",
                effort=effort or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IKEA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "creation": creation[:200],
            "ikea_effect_present": data.get("ikea_effect_present", False),
            "severity": data.get("severity", ""),
            "creator_valuation": data.get("creator_valuation", ""),
            "objective_valuation": data.get("objective_valuation", ""),
            "effort_invested": data.get("effort_invested", ""),
            "quality_gap": data.get("quality_gap", ""),
            "alternatives_available": data.get("alternatives_available", ""),
            "switching_cost": data.get("switching_cost", ""),
            "emotional_attachment": data.get("emotional_attachment", ""),
            "completion_status": data.get("completion_status", ""),
            "customization_value": data.get("customization_value", ""),
            "sunk_cost_interaction": data.get("sunk_cost_interaction", False),
            "recommendation": data.get("recommendation", ""),
        }

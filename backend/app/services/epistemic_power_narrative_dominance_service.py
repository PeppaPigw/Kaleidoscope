"""EpistemicPowerNarrativeDominanceService - Epistemic Power Narrative Dominance Detection.

Detects narrative dominance where dominant groups control the framing of issues.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POWER_NARRATIVE_DOMINANCE_SYSTEM = """You are an epistemic power and narrative dominance specialist. Given framing control, assess whether dominant groups control the framing of issues:

Key concepts:
- Narrative dominance: powerful groups control the story through which issues are understood
- Framing control: deciding what terms, causes, and stakes define the issue
- Alternative narrative suppression: excluding competing interpretations
- History writing privilege: controlling collective memory and causal accounts
- Definitional power: deciding what categories and labels count

When narrative dominance IS present:
- Dominant groups define the issue's meaning and stakes
- Alternative narratives are excluded, ridiculed, or made invisible
- History is written to preserve the dominant group's legitimacy
- Definitions are controlled to preclude challenges
- Affected groups cannot frame their own experience

When no narrative dominance:
- Multiple narratives can be heard and tested
- Affected groups participate in framing
- Historical accounts are contestable and evidence-based
- Definitions are transparent and open to challenge
- Dominant framing is treated as one perspective, not reality itself

Output JSON with: dominance_detected (bool), severity (none/mild/moderate/severe), framing_control (what framing is controlled), alternative_narrative_suppression (what alternatives are suppressed), history_writing_privilege (how history is controlled), definitional_power (what definitions are controlled), recommendation (no_dominance/mild_frame_pluralism/significant_narrative_opening/major_reframing_required/emergency_counter_narrative_access)."""

EPISTEMIC_POWER_NARRATIVE_DOMINANCE_PROMPT = """Detect epistemic power and narrative dominance:

Framing control: {framing_control}
Alternative narrative suppression: {alternative_narrative_suppression}
History writing privilege: {history_writing_privilege}
Definitional power: {definitional_power}
Domain: {domain}
Context: {context}

Are dominant groups controlling the framing of issues? Return ONLY valid JSON."""


class EpistemicPowerNarrativeDominanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        framing_control: str,
        *,
        alternative_narrative_suppression: str = "",
        history_writing_privilege: str = "",
        definitional_power: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POWER_NARRATIVE_DOMINANCE_PROMPT.format(
                framing_control=framing_control,
                alternative_narrative_suppression=alternative_narrative_suppression or "Not specified",
                history_writing_privilege=history_writing_privilege or "Not specified",
                definitional_power=definitional_power or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POWER_NARRATIVE_DOMINANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "framing_control": framing_control[:200],
            "dominance_detected": data.get("dominance_detected", False),
            "severity": data.get("severity", ""),
            "alternative_narrative_suppression": data.get("alternative_narrative_suppression", ""),
            "history_writing_privilege": data.get("history_writing_privilege", ""),
            "definitional_power": data.get("definitional_power", ""),
            "recommendation": data.get("recommendation", ""),
        }

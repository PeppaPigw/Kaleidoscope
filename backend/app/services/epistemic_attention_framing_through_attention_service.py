"""EpistemicAttentionFramingThroughAttentionService — Epistemic Attention Framing Through Attention Detection.

Detects epistemic framing through selective direction of attention toward
some aspects of evidence while making alternatives less visible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_FRAMING_THROUGH_ATTENTION_SYSTEM = """You are an epistemic attention framing through attention specialist. Given attention direction, assess framing by selective salience:

Key concepts:
- Framing through attention: selective attention direction shapes interpretation
- Attention direction: where inquiry is steered before evaluation begins
- Spotlight effect: highlighted facts feel more important than unhighlighted facts
- Agenda setting: repeated focus defines what questions are considered relevant
- Salience manipulation: visibility is engineered to change judgment

When attention framing IS present:
- Attention is selectively directed
- Highlighted evidence dominates interpretation
- Alternative frames are obscured
- Agenda setting narrows inquiry
- Salience is manipulated as evidence

When no attention framing:
- Multiple frames remain visible
- Attention tracks relevance, not steering
- Highlighting is separated from probative value
- Agenda effects are disclosed
- Salience manipulation is corrected

Output JSON with: framing_through_attention_detected (bool), severity (none/mild/moderate/severe), spotlight_effect (what highlighted facts dominate), agenda_setting (what questions are privileged), salience_manipulation (what visibility is engineered), recommendation (no_attention_framing/mild_frame_awareness/significant_alternative_frames/major_attention_rebalancing/emergency_complete_frame_reset)."""

EPISTEMIC_ATTENTION_FRAMING_THROUGH_ATTENTION_PROMPT = """Detect epistemic attention framing through attention:

Attention direction: {attention_direction}
Spotlight effect: {spotlight_effect}
Agenda setting: {agenda_setting}
Salience manipulation: {salience_manipulation}
Domain: {domain}
Context: {context}

Is selective attention direction framing the interpretation? Return ONLY valid JSON."""


class EpistemicAttentionFramingThroughAttentionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        attention_direction: str,
        *,
        spotlight_effect: str = "",
        agenda_setting: str = "",
        salience_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_FRAMING_THROUGH_ATTENTION_PROMPT.format(
                attention_direction=attention_direction,
                spotlight_effect=spotlight_effect or "Not specified",
                agenda_setting=agenda_setting or "Not specified",
                salience_manipulation=salience_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_FRAMING_THROUGH_ATTENTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "attention_direction": attention_direction[:200],
            "framing_through_attention_detected": data.get("framing_through_attention_detected", False),
            "severity": data.get("severity", ""),
            "spotlight_effect": data.get("spotlight_effect", ""),
            "agenda_setting": data.get("agenda_setting", ""),
            "salience_manipulation": data.get("salience_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }

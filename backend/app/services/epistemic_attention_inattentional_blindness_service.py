"""EpistemicAttentionInattentionalBlindnessService — Epistemic Attention Inattentional Blindness Detection.

Detects epistemic inattentional blindness where focus on one object or task
causes obvious other evidence to be missed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_INATTENTIONAL_BLINDNESS_SYSTEM = """You are an epistemic attention inattentional blindness specialist. Given focus patterns, assess focus-induced omission:

Key concepts:
- Inattentional blindness: focus on one thing causes missing obvious others
- Focus-induced blindness: attention target blocks awareness of visible evidence
- Gorilla effect: unexpected but important evidence is missed
- Change blindness: meaningful changes are not noticed
- Expectation filtering: expected categories determine what is perceived

When inattentional blindness IS present:
- Narrow focus excludes obvious evidence
- Unexpected signals are missed
- Changes go unnoticed
- Expectations filter perception
- Confidence remains high despite omissions

When no inattentional blindness:
- Focus is balanced with peripheral scanning
- Unexpected evidence is noticed
- Change detection is active
- Expectations are treated as hypotheses
- Confidence accounts for attention limits

Output JSON with: inattentional_blindness_detected (bool), severity (none/mild/moderate/severe), gorilla_effect (what unexpected evidence was missed), change_blindness (what changes were missed), expectation_filtering (what expectations filtered perception), recommendation (no_inattentional_blindness/mild_peripheral_scan/significant_attention_widening/major_blind_spot_review/emergency_complete_attention_reset)."""

EPISTEMIC_ATTENTION_INATTENTIONAL_BLINDNESS_PROMPT = """Detect epistemic attention inattentional blindness:

Focus-induced blindness: {focus_induced_blindness}
Gorilla effect: {gorilla_effect}
Change blindness: {change_blindness}
Expectation filtering: {expectation_filtering}
Domain: {domain}
Context: {context}

Is focus on one thing causing obvious other evidence to be missed? Return ONLY valid JSON."""


class EpistemicAttentionInattentionalBlindnessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        focus_induced_blindness: str,
        *,
        gorilla_effect: str = "",
        change_blindness: str = "",
        expectation_filtering: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_INATTENTIONAL_BLINDNESS_PROMPT.format(
                focus_induced_blindness=focus_induced_blindness,
                gorilla_effect=gorilla_effect or "Not specified",
                change_blindness=change_blindness or "Not specified",
                expectation_filtering=expectation_filtering or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_INATTENTIONAL_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "focus_induced_blindness": focus_induced_blindness[:200],
            "inattentional_blindness_detected": data.get("inattentional_blindness_detected", False),
            "severity": data.get("severity", ""),
            "gorilla_effect": data.get("gorilla_effect", ""),
            "change_blindness": data.get("change_blindness", ""),
            "expectation_filtering": data.get("expectation_filtering", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMagicalThinkingHopeService — Epistemic Magical Thinking Hope Detection.

Detects epistemic magical thinking hope — hope based on magical rather
than rational thinking about intellectual outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MAGICAL_THINKING_HOPE_SYSTEM = """You are an epistemic magical thinking hope specialist. Given hope based on magical thinking, assess magical thinking hope:

Key concepts:
- Epistemic magical thinking hope: hope based on magical not rational thinking
- Causation confusion: believing wanting makes it happen
- Ritual thinking: performing intellectual rituals for outcomes
- Superstitious reasoning: connecting unrelated events to outcomes
- Omnipotence fantasy: believing thought alone changes reality
- Symbolic causation: treating symbols as causes
- Wish fulfillment logic: expecting wishes to become reality

When epistemic magical thinking hope IS present:
- Hope based on magical thinking
- Believing wanting makes happen
- Performing rituals for outcomes
- Connecting unrelated events
- Believing thought changes reality
- Treating symbols as causes
- Expecting wishes to become reality

When no magical thinking hope:
- Hope based on evidence
- Understanding causation
- Action-based approach
- Recognizing randomness
- Realistic about thought's limits
- Understanding symbolism
- Working toward outcomes

Output JSON with: magical_thinking_hope_detected (bool), severity (none/mild/moderate/severe), causation_confusion (what believing wanting causes), ritual_thinking (what rituals performing), omnipotence_fantasy (what believing thought changes), wish_fulfillment_logic (what expecting wishes to cause), recommendation (no_magical_thinking_hope/mild_reality_grounding/significant_causation_education/major_intensive_magical_thinking_processing/emergency_severe_reality_disconnect)."""

EPISTEMIC_MAGICAL_THINKING_HOPE_PROMPT = """Detect epistemic magical thinking hope:

Causation confusion: {causation_confusion}
Ritual thinking: {ritual_thinking}
Omnipotence fantasy: {omnipotence_fantasy}
Wish fulfillment logic: {wish_fulfillment_logic}
Domain: {domain}
Context: {context}

Is there hope based on magical rather than rational thinking? Return ONLY valid JSON."""


class EpistemicMagicalThinkingHopeService:
    """Detects epistemic magical thinking hope — hope based on magical thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        causation_confusion: str,
        *,
        ritual_thinking: str = "",
        omnipotence_fantasy: str = "",
        wish_fulfillment_logic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic magical thinking hope."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MAGICAL_THINKING_HOPE_PROMPT.format(
                causation_confusion=causation_confusion,
                ritual_thinking=ritual_thinking or "Not specified",
                omnipotence_fantasy=omnipotence_fantasy or "Not specified",
                wish_fulfillment_logic=wish_fulfillment_logic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MAGICAL_THINKING_HOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "causation_confusion": causation_confusion[:200],
            "magical_thinking_hope_detected": data.get("magical_thinking_hope_detected", False),
            "severity": data.get("severity", ""),
            "ritual_thinking": data.get("ritual_thinking", ""),
            "omnipotence_fantasy": data.get("omnipotence_fantasy", ""),
            "wish_fulfillment_logic": data.get("wish_fulfillment_logic", ""),
            "recommendation": data.get("recommendation", ""),
        }

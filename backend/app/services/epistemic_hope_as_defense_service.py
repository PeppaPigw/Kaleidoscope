"""EpistemicHopeAsDefenseService — Epistemic Hope As Defense Detection.

Detects epistemic hope as defense — using hope to avoid confronting
difficult intellectual truths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HOPE_AS_DEFENSE_SYSTEM = """You are an epistemic hope as defense specialist. Given hope used to avoid difficult truths, assess hope as defense:

Key concepts:
- Epistemic hope as defense: using hope to avoid difficult truths
- Avoidance through optimism: staying positive to not face reality
- Future focus escape: looking ahead to avoid present truth
- Possibility as shield: using what could be to block what is
- Defensive hopefulness: hope that prevents necessary grief
- Truth postponement: hoping to delay confronting reality
- Comfort maintenance: hope serving comfort not truth

When epistemic hope as defense IS present:
- Using hope to avoid truths
- Staying positive to not face reality
- Looking ahead to avoid present
- Using possibility to block reality
- Hope preventing necessary grief
- Hoping to delay confronting
- Hope serving comfort not truth

When no hope as defense:
- Hope alongside truth
- Positive while facing reality
- Present and future balanced
- Possibility and reality coexisting
- Hope allowing grief
- Confronting while hoping
- Hope serving truth

Output JSON with: hope_as_defense_detected (bool), severity (none/mild/moderate/severe), avoidance_through_optimism (what staying positive to avoid), future_focus_escape (what looking ahead to avoid), defensive_hopefulness (what preventing grief about), truth_postponement (what delaying confronting), recommendation (no_hope_as_defense/mild_truth_integration/significant_reality_facing/major_intensive_defense_processing/emergency_severe_avoidance)."""

EPISTEMIC_HOPE_AS_DEFENSE_PROMPT = """Detect epistemic hope as defense:

Avoidance through optimism: {avoidance_through_optimism}
Future focus escape: {future_focus_escape}
Defensive hopefulness: {defensive_hopefulness}
Truth postponement: {truth_postponement}
Domain: {domain}
Context: {context}

Is there using hope to avoid confronting difficult truths? Return ONLY valid JSON."""


class EpistemicHopeAsDefenseService:
    """Detects epistemic hope as defense — using hope to avoid difficult truths."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        avoidance_through_optimism: str,
        *,
        future_focus_escape: str = "",
        defensive_hopefulness: str = "",
        truth_postponement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hope as defense."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HOPE_AS_DEFENSE_PROMPT.format(
                avoidance_through_optimism=avoidance_through_optimism,
                future_focus_escape=future_focus_escape or "Not specified",
                defensive_hopefulness=defensive_hopefulness or "Not specified",
                truth_postponement=truth_postponement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HOPE_AS_DEFENSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "avoidance_through_optimism": avoidance_through_optimism[:200],
            "hope_as_defense_detected": data.get("hope_as_defense_detected", False),
            "severity": data.get("severity", ""),
            "future_focus_escape": data.get("future_focus_escape", ""),
            "defensive_hopefulness": data.get("defensive_hopefulness", ""),
            "truth_postponement": data.get("truth_postponement", ""),
            "recommendation": data.get("recommendation", ""),
        }

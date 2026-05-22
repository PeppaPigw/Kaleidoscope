"""EpistemicFugueService — Epistemic Fugue Detection.

Detects epistemic fugue — sudden departure from one's intellectual identity
or position without awareness, adopting a completely different stance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FUGUE_SYSTEM = """You are an epistemic fugue specialist. Given sudden departure from intellectual identity, assess fugue:

Key concepts:
- Epistemic fugue: sudden departure from intellectual position
- Identity switch: becoming different intellectual person
- Awareness gap: not realizing the departure
- Position abandonment: leaving established stance without reason
- Confusion on return: bewildered when original position resurfaces
- Travel: moving to completely different intellectual territory
- Amnesia for departure: not remembering leaving original position

When epistemic fugue IS present:
- Sudden departure from position
- Becoming different person
- Not realizing departure
- Leaving stance without reason
- Bewildered on return
- Moving to different territory
- Not remembering leaving

When no fugue:
- Stable intellectual position
- Consistent identity
- Aware of changes
- Reasoned position shifts
- Continuous awareness
- Gradual exploration
- Remembering transitions

Output JSON with: fugue_detected (bool), severity (none/mild/moderate/severe), identity_switch (what becoming), awareness_gap (what not realizing), position_abandonment (what leaving), amnesia_pattern (what not remembering), recommendation (no_fugue/mild_continuity_practice/significant_identity_stabilization/major_intensive_dissociation_therapy/emergency_severe_fugue)."""

EPISTEMIC_FUGUE_PROMPT = """Detect epistemic fugue:

Identity switch: {identity_switch}
Awareness gap: {awareness_gap}
Position abandonment: {position_abandonment}
Amnesia pattern: {amnesia_pattern}
Domain: {domain}
Context: {context}

Is there sudden departure from intellectual identity without awareness? Return ONLY valid JSON."""


class EpistemicFugueService:
    """Detects epistemic fugue — sudden departure from intellectual identity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        identity_switch: str,
        *,
        awareness_gap: str = "",
        position_abandonment: str = "",
        amnesia_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fugue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FUGUE_PROMPT.format(
                identity_switch=identity_switch,
                awareness_gap=awareness_gap or "Not specified",
                position_abandonment=position_abandonment or "Not specified",
                amnesia_pattern=amnesia_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FUGUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "identity_switch": identity_switch[:200],
            "fugue_detected": data.get("fugue_detected", False),
            "severity": data.get("severity", ""),
            "awareness_gap": data.get("awareness_gap", ""),
            "position_abandonment": data.get("position_abandonment", ""),
            "amnesia_pattern": data.get("amnesia_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }

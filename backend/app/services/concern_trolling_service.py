"""ConcernTrollingService — Concern Trolling Detection.

Detects concern trolling — feigning concern for a group or cause
in order to undermine it from within. The concern troll poses as
a sympathetic ally while actually working to weaken, divide, or
discredit the group they claim to support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONCERN_TROLLING_SYSTEM = """You are a concern trolling specialist. Given a communication pattern, assess whether expressed concern is genuine or is being used to undermine:

Key concepts:
- Concern trolling: feigning concern to undermine from within
- False ally: posing as supporter while working against
- Sealioning overlap: bad-faith engagement disguised as good faith
- Divide and conquer: using "concern" to create internal divisions
- Tone trolling overlap: "I'm worried about how this looks"
- Undermining through "help": suggestions that weaken rather than strengthen
- Plausible deniability: "I'm just trying to help" as cover

When concern trolling IS present:
- "As a supporter, I'm worried that..." followed by undermining suggestions
- Concern that consistently leads to inaction or weakening
- The "concerned" party has no stake in the group's success
- Suggestions that would divide or weaken if followed
- Pattern of raising concerns that serve opponents' interests
- "I'm on your side, but..." followed by opponent's talking points
- Concern that never leads to constructive action

When concern IS genuine:
- The person has demonstrated commitment to the cause
- Their concerns are specific and actionable
- They offer solutions alongside problems
- Their track record shows genuine support
- The concerns would strengthen the group if addressed
- They're willing to do work to address their concerns
- The concerns don't consistently serve opponents' interests

Output JSON with: concern_trolling_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), expressed_concern (what concern is expressed), actual_effect (what effect would following the advice have), track_record (does the person have genuine commitment), cui_bono (who benefits from this concern), recommendation (concern_genuine/mild_undermining/significant_concern_trolling/major_false_ally/evaluate_track_record_and_effects)."""

CONCERN_TROLLING_PROMPT = """Detect concern trolling:

Communication: {communication}
Concern: {concern}
Effect: {effect}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is expressed concern being used to undermine rather than help? Return ONLY valid JSON."""


class ConcernTrollingService:
    """Detects concern trolling — feigning concern to undermine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        concern: str = "",
        effect: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect concern trolling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONCERN_TROLLING_PROMPT.format(
                communication=communication,
                concern=concern or "Not specified",
                effect=effect or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONCERN_TROLLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "concern_trolling_present": data.get("concern_trolling_present", False),
            "severity": data.get("severity", ""),
            "expressed_concern": data.get("expressed_concern", ""),
            "actual_effect": data.get("actual_effect", ""),
            "cui_bono": data.get("cui_bono", ""),
            "recommendation": data.get("recommendation", ""),
        }

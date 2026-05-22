"""NextInLineService — Next-in-Line Effect Detection.

Detects the next-in-line effect — failing to process information
from others because one is mentally rehearsing one's own
upcoming contribution. Brenner (1973). In meetings, presentations,
and discussions, people miss what's said right before their turn
because they're preparing what they'll say. Attention consumed
by self-preparation at the cost of listening.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NEXT_IN_LINE_SYSTEM = """You are a next-in-line effect specialist. Given a communication or meeting situation, assess whether the next-in-line effect is causing information loss:

Key concepts (Brenner, 1973):
- Next-in-line effect: missing others' input while preparing own
- Self-focused attention: rehearsal consuming processing capacity
- Performance anxiety: worry about own turn blocking listening
- Sequential presentation: structured turn-taking amplifies effect
- Dual-task interference: can't fully listen while preparing
- Meeting blindness: missing key points said just before your turn
- Preparation tunnel: narrowing attention to own contribution

When the next-in-line effect IS present:
- "What did they just say?" right before one's own turn
- Missing key points from the previous speaker in meetings
- Preparing responses instead of listening to current speaker
- Inability to summarize what was said immediately before one's contribution
- Asking questions that were already answered moments ago
- Repeating points already made by the previous speaker
- Better recall of speakers far from one's own position

When attention IS appropriately managed:
- Active listening maintained regardless of upcoming turn
- Notes taken on others' contributions even when preparing
- Ability to reference and build on immediately preceding points
- Preparation done in advance rather than during others' turns
- Explicit acknowledgment of previous speaker's points

Output JSON with: next_in_line_present (bool), severity (none/mild/moderate/severe), situation (what communication context), preparation_focus (what is being rehearsed), missed_content (what information was missed), position_effect (how does turn order affect attention), anxiety_level (performance anxiety contributing), mitigation (what could reduce the effect), recommendation (attention_well_managed/mild_preparation_distraction/significant_next_in_line_effect/major_listening_failure/separate_preparation_from_listening)."""

NEXT_IN_LINE_PROMPT = """Detect next-in-line effect:

Situation: {situation}
Turn structure: {structure}
Preparation: {preparation}
Missed info: {missed}
Domain: {domain}
Context: {context}

Is mental rehearsal of one's own upcoming contribution causing failure to process others' input? Return ONLY valid JSON."""


class NextInLineService:
    """Detects next-in-line effect — missing others' input while preparing own turn."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        structure: str = "",
        preparation: str = "",
        missed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect next-in-line effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NEXT_IN_LINE_PROMPT.format(
                situation=situation,
                structure=structure or "Not specified",
                preparation=preparation or "Not specified",
                missed=missed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NEXT_IN_LINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "next_in_line_present": data.get("next_in_line_present", False),
            "severity": data.get("severity", ""),
            "preparation_focus": data.get("preparation_focus", ""),
            "missed_content": data.get("missed_content", ""),
            "position_effect": data.get("position_effect", ""),
            "anxiety_level": data.get("anxiety_level", ""),
            "mitigation": data.get("mitigation", ""),
            "recommendation": data.get("recommendation", ""),
        }

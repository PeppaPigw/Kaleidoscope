"""StandpointBlindnessService — Standpoint Blindness Detection.

Detects standpoint blindness — inability to recognize how one's
social position shapes what one can see and know, treating one's
perspective as neutral or objective.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STANDPOINT_BLINDNESS_SYSTEM = """You are a standpoint blindness specialist. Given a claim or analysis, assess whether the analyst's social position is shaping their perspective without acknowledgment:

Key concepts:
- Standpoint blindness: not seeing how position shapes perspective
- Situated knowledge: all knowledge is from somewhere
- View from nowhere: claiming objectivity from a specific position
- Positional privilege: some positions see more, some less
- Unmarked perspective: treating one's view as neutral
- Social location: how identity shapes what's visible
- Epistemic privilege/limitation: what position enables/prevents seeing

When standpoint blindness IS present:
- Analyst's position shapes conclusions without acknowledgment
- Perspective treated as neutral or objective
- Social location invisible to the analyst
- What's visible from one position treated as all there is
- Privilege of position unrecognized
- Limitations of standpoint not acknowledged
- View from specific position presented as view from nowhere

When perspective is appropriately situated:
- Analyst's position acknowledged
- Limitations of standpoint stated
- Multiple perspectives sought
- Situated nature of knowledge recognized
- Privilege of position acknowledged
- What can't be seen from this position noted
- Objectivity pursued through multiple standpoints

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), analysis (what is analyzed), standpoint (what standpoint shapes the analysis), invisible (what is invisible from this standpoint), unmarked (what perspective is treated as neutral), recommendation (appropriate_situated_analysis/mild_position_unawareness/significant_standpoint_blindness/major_false_objectivity/acknowledge_standpoint)."""

STANDPOINT_BLINDNESS_PROMPT = """Detect standpoint blindness:

Analysis: {analysis}
Analyst position: {position}
Perspective claimed: {perspective}
What's invisible: {invisible}
Domain: {domain}
Context: {context}

Is the analyst's social position shaping their perspective without acknowledgment? Return ONLY valid JSON."""


class StandpointBlindnessService:
    """Detects standpoint blindness — not seeing how position shapes perspective."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        position: str = "",
        perspective: str = "",
        invisible: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect standpoint blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STANDPOINT_BLINDNESS_PROMPT.format(
                analysis=analysis,
                position=position or "Not specified",
                perspective=perspective or "Not specified",
                invisible=invisible or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STANDPOINT_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "standpoint": data.get("standpoint", ""),
            "invisible": data.get("invisible", ""),
            "unmarked": data.get("unmarked", ""),
            "recommendation": data.get("recommendation", ""),
        }

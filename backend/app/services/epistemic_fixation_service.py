"""EpistemicFixationService — Epistemic Fixation Detection.

Detects epistemic fixation — becoming stuck at a particular intellectual
developmental stage, unable to progress to more sophisticated thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FIXATION_SYSTEM = """You are an epistemic fixation specialist. Given intellectual developmental stuckness, assess fixation:

Key concepts:
- Epistemic fixation: stuck at particular developmental stage
- Repetition compulsion: returning to same intellectual patterns
- Growth resistance: refusing to develop further
- Comfort zone rigidity: cannot leave familiar thinking
- Stage-inappropriate: using methods below capacity
- Unresolved conflict: earlier stage issue blocking progress
- Developmental arrest: growth stopped at specific point

When epistemic fixation IS present:
- Stuck at particular stage
- Returning to same patterns
- Refusing to develop
- Cannot leave familiar thinking
- Using methods below capacity
- Earlier issue blocking
- Growth stopped

When no fixation:
- Progressing normally
- New patterns emerging
- Developing further
- Exploring new thinking
- Using full capacity
- No blocking issues
- Continuous growth

Output JSON with: fixation_detected (bool), severity (none/mild/moderate/severe), stuck_stage (what particular stage), repetition_pattern (what returning), growth_resistance (what refusing), unresolved_conflict (what blocking), recommendation (no_fixation/mild_growth_encouragement/significant_developmental_therapy/major_intensive_unsticking/emergency_complete_arrest)."""

EPISTEMIC_FIXATION_PROMPT = """Detect epistemic fixation:

Stuck stage: {stuck_stage}
Repetition pattern: {repetition_pattern}
Growth resistance: {growth_resistance}
Unresolved conflict: {unresolved_conflict}
Domain: {domain}
Context: {context}

Is there being stuck at a particular intellectual developmental stage? Return ONLY valid JSON."""


class EpistemicFixationService:
    """Detects epistemic fixation — stuck at intellectual developmental stage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stuck_stage: str,
        *,
        repetition_pattern: str = "",
        growth_resistance: str = "",
        unresolved_conflict: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fixation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FIXATION_PROMPT.format(
                stuck_stage=stuck_stage,
                repetition_pattern=repetition_pattern or "Not specified",
                growth_resistance=growth_resistance or "Not specified",
                unresolved_conflict=unresolved_conflict or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FIXATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stuck_stage": stuck_stage[:200],
            "fixation_detected": data.get("fixation_detected", False),
            "severity": data.get("severity", ""),
            "repetition_pattern": data.get("repetition_pattern", ""),
            "growth_resistance": data.get("growth_resistance", ""),
            "unresolved_conflict": data.get("unresolved_conflict", ""),
            "recommendation": data.get("recommendation", ""),
        }

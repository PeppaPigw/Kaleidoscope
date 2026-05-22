"""EpistemicAbstractionLadderFailureService — Epistemic Abstraction Ladder Failure Detection.

Detects epistemic abstraction ladder failure — inability to move fluidly
between abstraction levels as the situation demands.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABSTRACTION_LADDER_FAILURE_SYSTEM = """You are an epistemic abstraction ladder failure specialist. Given inability to move between abstraction levels, assess ladder failure:

Key concepts:
- Epistemic abstraction ladder failure: inability to move fluidly between levels
- Level rigidity: stuck at one level of abstraction
- Zoom failure: unable to zoom in or out as needed
- Translation inability: unable to translate between levels
- Context-level mismatch: using wrong level for the context
- Granularity fixation: fixated on one granularity
- Perspective lock: locked into one perspective level

When epistemic abstraction ladder failure IS present:
- Unable to move between levels
- Stuck at one level
- Cannot zoom in or out
- Cannot translate between levels
- Wrong level for context
- Fixated on one granularity
- Locked into one perspective

When no ladder failure:
- Fluid movement between levels
- Appropriate level chosen
- Can zoom in and out
- Translates between levels
- Right level for context
- Granularity adjusted
- Perspective flexible

Output JSON with: abstraction_ladder_failure_detected (bool), severity (none/mild/moderate/severe), level_rigidity (what level stuck at), zoom_failure (what zoom failing), translation_inability (what translation failing), context_level_mismatch (what mismatch), recommendation (no_ladder_failure/mild_level_practice/significant_fluidity_recovery/major_intensive_level_training/emergency_complete_ladder_failure)."""

EPISTEMIC_ABSTRACTION_LADDER_FAILURE_PROMPT = """Detect epistemic abstraction ladder failure:

Level rigidity: {level_rigidity}
Zoom failure: {zoom_failure}
Translation inability: {translation_inability}
Context-level mismatch: {context_level_mismatch}
Domain: {domain}
Context: {context}

Is there inability to move fluidly between abstraction levels? Return ONLY valid JSON."""


class EpistemicAbstractionLadderFailureService:
    """Detects epistemic abstraction ladder failure — level rigidity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        level_rigidity: str,
        *,
        zoom_failure: str = "",
        translation_inability: str = "",
        context_level_mismatch: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic abstraction ladder failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABSTRACTION_LADDER_FAILURE_PROMPT.format(
                level_rigidity=level_rigidity,
                zoom_failure=zoom_failure or "Not specified",
                translation_inability=translation_inability or "Not specified",
                context_level_mismatch=context_level_mismatch or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABSTRACTION_LADDER_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "level_rigidity": level_rigidity[:200],
            "abstraction_ladder_failure_detected": data.get("abstraction_ladder_failure_detected", False),
            "severity": data.get("severity", ""),
            "zoom_failure": data.get("zoom_failure", ""),
            "translation_inability": data.get("translation_inability", ""),
            "context_level_mismatch": data.get("context_level_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }

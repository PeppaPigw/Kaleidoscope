"""EpistemicEmotionAnxietyDrivenCertaintyService - Epistemic Emotion Anxiety-Driven Certainty Detection.

Detects anxiety-driven certainty seeking where discomfort with uncertainty drives premature closure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTION_ANXIETY_DRIVEN_CERTAINTY_SYSTEM = """You are an epistemic emotion anxiety-driven certainty specialist. Given uncertainty intolerance, assess anxiety-driven certainty seeking:

Key concepts:
- Epistemic emotion anxiety-driven certainty: discomfort with uncertainty driving premature closure
- Uncertainty intolerance: inability to remain with unresolved ambiguity
- Anxiety reduction through belief: belief adopted because it calms anxiety
- False certainty comfort: certainty valued for relief rather than truth
- Ambiguity aversion: ambiguous possibilities rejected too quickly

When anxiety-driven certainty IS present:
- Uncertainty intolerance drives belief
- Closure is reached prematurely
- Belief reduces anxiety more than it tracks evidence
- False certainty feels comforting
- Ambiguity is avoided rather than examined

When no anxiety-driven certainty:
- Uncertainty is tolerated
- Closure follows evidence
- Emotional relief is separated from truth
- Confidence remains calibrated
- Ambiguity is examined directly

Output JSON with: anxiety_driven_certainty_detected (bool), severity (none/mild/moderate/severe), anxiety_reduction_through_belief (what belief reduces anxiety), false_certainty_comfort (what certainty is comforting), ambiguity_aversion (what ambiguity is avoided), recommendation (no_anxiety_driven_certainty/mild_uncertainty_tolerance/significant_closure_delay/major_ambiguity_work/emergency_complete_anxiety_certainty)."""

EPISTEMIC_EMOTION_ANXIETY_DRIVEN_CERTAINTY_PROMPT = """Detect epistemic emotion anxiety-driven certainty:

Uncertainty intolerance: {uncertainty_intolerance}
Anxiety reduction through belief: {anxiety_reduction_through_belief}
False certainty comfort: {false_certainty_comfort}
Ambiguity aversion: {ambiguity_aversion}
Domain: {domain}
Context: {context}

Is discomfort with uncertainty driving premature closure? Return ONLY valid JSON."""


class EpistemicEmotionAnxietyDrivenCertaintyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        uncertainty_intolerance: str,
        *,
        anxiety_reduction_through_belief: str = "",
        false_certainty_comfort: str = "",
        ambiguity_aversion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTION_ANXIETY_DRIVEN_CERTAINTY_PROMPT.format(
                uncertainty_intolerance=uncertainty_intolerance,
                anxiety_reduction_through_belief=anxiety_reduction_through_belief or "Not specified",
                false_certainty_comfort=false_certainty_comfort or "Not specified",
                ambiguity_aversion=ambiguity_aversion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTION_ANXIETY_DRIVEN_CERTAINTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "uncertainty_intolerance": uncertainty_intolerance[:200],
            "anxiety_driven_certainty_detected": data.get("anxiety_driven_certainty_detected", False),
            "severity": data.get("severity", ""),
            "anxiety_reduction_through_belief": data.get("anxiety_reduction_through_belief", ""),
            "false_certainty_comfort": data.get("false_certainty_comfort", ""),
            "ambiguity_aversion": data.get("ambiguity_aversion", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicScaleLevelConfusionService — Epistemic Scale Level Confusion Detection.

Detects epistemic scale level confusion — confusing explanations at different
levels of analysis (biological vs. psychological, individual vs. structural).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_LEVEL_CONFUSION_SYSTEM = """You are an epistemic scale level confusion specialist. Given level confusion, assess cross-level inference errors:

Key concepts:
- Epistemic level confusion: mixing explanatory levels inappropriately
- Reductive explanation: explaining higher-level phenomena only at lower level
- Eliminative reasoning: denying higher-level phenomena exist
- Upward causation only: ignoring downward causation from system to parts
- Level-inappropriate intervention: intervening at wrong level for the problem
- Explanatory imperialism: one level claiming to explain everything
- Category mistake: applying concepts from one level to another

When epistemic level confusion IS present:
- Explanatory levels mixed
- Reduction inappropriate
- Higher levels eliminated
- Downward causation ignored
- Interventions at wrong level
- One level dominating
- Category mistakes made

When no level confusion:
- Levels distinguished
- Appropriate reduction
- Multiple levels respected
- Bidirectional causation
- Level-appropriate intervention
- Explanatory pluralism
- Categories respected

Output JSON with: level_confusion_detected (bool), severity (none/mild/moderate/severe), reductive_explanation (what inappropriately reduced), eliminative_reasoning (what eliminated), level_inappropriate_intervention (what wrong-level intervention), explanatory_imperialism (what level dominating), recommendation (no_level_confusion/mild_level_awareness/significant_multi_level_analysis/major_intensive_level_integration/emergency_complete_level_confusion)."""

EPISTEMIC_SCALE_LEVEL_CONFUSION_PROMPT = """Detect epistemic scale level confusion:

Reductive explanation: {reductive_explanation}
Eliminative reasoning: {eliminative_reasoning}
Level-inappropriate intervention: {level_inappropriate_intervention}
Explanatory imperialism: {explanatory_imperialism}
Domain: {domain}
Context: {context}

Are explanatory levels being confused or inappropriately mixed? Return ONLY valid JSON."""


class EpistemicScaleLevelConfusionService:
    """Detects epistemic scale level confusion — cross-level errors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reductive_explanation: str,
        *,
        eliminative_reasoning: str = "",
        level_inappropriate_intervention: str = "",
        explanatory_imperialism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scale level confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_LEVEL_CONFUSION_PROMPT.format(
                reductive_explanation=reductive_explanation,
                eliminative_reasoning=eliminative_reasoning or "Not specified",
                level_inappropriate_intervention=level_inappropriate_intervention or "Not specified",
                explanatory_imperialism=explanatory_imperialism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_LEVEL_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reductive_explanation": reductive_explanation[:200],
            "level_confusion_detected": data.get("level_confusion_detected", False),
            "severity": data.get("severity", ""),
            "eliminative_reasoning": data.get("eliminative_reasoning", ""),
            "level_inappropriate_intervention": data.get("level_inappropriate_intervention", ""),
            "explanatory_imperialism": data.get("explanatory_imperialism", ""),
            "recommendation": data.get("recommendation", ""),
        }

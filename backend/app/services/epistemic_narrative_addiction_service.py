"""EpistemicNarrativeAddictionService — Epistemic Narrative Addiction Detection.

Detects epistemic narrative addiction — addicted to narrative coherence
at the expense of truth and accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_ADDICTION_SYSTEM = """You are an epistemic narrative addiction specialist. Given addiction to narrative coherence over truth, assess narrative addiction:

Key concepts:
- Epistemic narrative addiction: addicted to narrative coherence over truth
- Story over facts: preferring good story over accurate facts
- Coherence craving: craving coherence even when reality is incoherent
- Plot dependency: needing events to follow a plot
- Meaning manufacture: manufacturing meaning where none exists
- Pattern imposition: imposing patterns on randomness
- Narrative satisfaction: prioritizing narrative satisfaction over truth

When epistemic narrative addiction IS present:
- Addicted to coherence over truth
- Preferring story over facts
- Craving coherence in incoherent reality
- Needing events to follow plot
- Manufacturing meaning
- Imposing patterns on randomness
- Prioritizing satisfaction over truth

When no narrative addiction:
- Truth over coherence
- Facts over story
- Comfortable with incoherence
- Accepting plotless events
- Finding genuine meaning
- Recognizing randomness
- Truth over satisfaction

Output JSON with: narrative_addiction_detected (bool), severity (none/mild/moderate/severe), story_over_facts (what story preferred over facts), coherence_craving (what coherence craved about), meaning_manufacture (what meaning manufactured), pattern_imposition (what patterns imposed on), recommendation (no_narrative_addiction/mild_truth_practice/significant_incoherence_tolerance/major_intensive_narrative_detachment/emergency_complete_narrative_addiction)."""

EPISTEMIC_NARRATIVE_ADDICTION_PROMPT = """Detect epistemic narrative addiction:

Story over facts: {story_over_facts}
Coherence craving: {coherence_craving}
Meaning manufacture: {meaning_manufacture}
Pattern imposition: {pattern_imposition}
Domain: {domain}
Context: {context}

Is there addiction to narrative coherence at the expense of truth? Return ONLY valid JSON."""


class EpistemicNarrativeAddictionService:
    """Detects epistemic narrative addiction — addicted to coherence over truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        story_over_facts: str,
        *,
        coherence_craving: str = "",
        meaning_manufacture: str = "",
        pattern_imposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_ADDICTION_PROMPT.format(
                story_over_facts=story_over_facts,
                coherence_craving=coherence_craving or "Not specified",
                meaning_manufacture=meaning_manufacture or "Not specified",
                pattern_imposition=pattern_imposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "story_over_facts": story_over_facts[:200],
            "narrative_addiction_detected": data.get("narrative_addiction_detected", False),
            "severity": data.get("severity", ""),
            "coherence_craving": data.get("coherence_craving", ""),
            "meaning_manufacture": data.get("meaning_manufacture", ""),
            "pattern_imposition": data.get("pattern_imposition", ""),
            "recommendation": data.get("recommendation", ""),
        }

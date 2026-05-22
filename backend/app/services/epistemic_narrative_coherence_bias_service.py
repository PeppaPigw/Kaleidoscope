"""EpistemicNarrativeCoherenceBiasService — Epistemic Narrative Coherence Bias Detection.

Detects epistemic narrative coherence bias — preferring coherent stories
over accurate but fragmented evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_COHERENCE_BIAS_SYSTEM = """You are an epistemic narrative coherence bias specialist. Given preference for coherent stories over fragmented evidence, assess narrative coherence bias:

Key concepts:
- Epistemic narrative coherence bias: preferring coherent stories over accurate fragmented evidence
- Story preference: choosing narrative completeness over evidential accuracy
- Coherence over truth: valuing how well pieces fit together over whether pieces are true
- Gap filling: filling evidential gaps with narrative logic rather than admitting uncertainty
- Contradiction smoothing: smoothing over contradictions to maintain narrative flow
- Selective inclusion: including only evidence that fits the story
- Narrative seduction: being seduced by elegant narratives despite weak evidence

When epistemic narrative coherence bias IS present:
- Coherent stories preferred over fragmented truth
- Narrative completeness valued over accuracy
- Gaps filled with story logic
- Contradictions smoothed over
- Evidence selectively included for narrative fit
- Elegant narratives accepted despite weak evidence
- Fragmented but accurate evidence dismissed

When no narrative coherence bias:
- Truth preferred over coherence
- Fragmented evidence accepted when accurate
- Gaps acknowledged as uncertainty
- Contradictions preserved and examined
- All evidence considered regardless of narrative fit
- Narrative elegance not confused with truth
- Incomplete pictures accepted

Output JSON with: narrative_coherence_bias_detected (bool), severity (none/mild/moderate/severe), story_preference (what story preferred over evidence), gap_filling (what gaps filled narratively), contradiction_smoothing (what contradictions smoothed), selective_inclusion (what selectively included), recommendation (no_narrative_coherence_bias/mild_evidence_priority_practice/significant_fragmentation_tolerance/major_intensive_truth_over_coherence/emergency_complete_narrative_coherence_bias)."""

EPISTEMIC_NARRATIVE_COHERENCE_BIAS_PROMPT = """Detect epistemic narrative coherence bias:

Story preference: {story_preference}
Gap filling: {gap_filling}
Contradiction smoothing: {contradiction_smoothing}
Selective inclusion: {selective_inclusion}
Domain: {domain}
Context: {context}

Are coherent stories being preferred over accurate but fragmented evidence? Return ONLY valid JSON."""


class EpistemicNarrativeCoherenceBiasService:
    """Detects epistemic narrative coherence bias — story over evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        story_preference: str,
        *,
        gap_filling: str = "",
        contradiction_smoothing: str = "",
        selective_inclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative coherence bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_COHERENCE_BIAS_PROMPT.format(
                story_preference=story_preference,
                gap_filling=gap_filling or "Not specified",
                contradiction_smoothing=contradiction_smoothing or "Not specified",
                selective_inclusion=selective_inclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_COHERENCE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "story_preference": story_preference[:200],
            "narrative_coherence_bias_detected": data.get("narrative_coherence_bias_detected", False),
            "severity": data.get("severity", ""),
            "gap_filling": data.get("gap_filling", ""),
            "contradiction_smoothing": data.get("contradiction_smoothing", ""),
            "selective_inclusion": data.get("selective_inclusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

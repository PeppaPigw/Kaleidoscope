"""EpistemicNarrativeConstructionCoherenceBiasService - Epistemic Narrative Construction Coherence Bias Detection.

Detects preference for coherent narratives over accurate but messy accounts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CONSTRUCTION_COHERENCE_BIAS_SYSTEM = """You are an epistemic narrative construction coherence bias specialist. Given a preference for coherent narratives, assess whether coherence is being prioritized over accuracy:

Key concepts:
- Epistemic narrative construction coherence bias: preferring a coherent story over accurate but messy evidence
- Loose-end intolerance: discomfort with unresolved details
- Narrative smoothing: removing friction, contradiction, or awkwardness to preserve story flow
- Complexity rejection: dismissing messy accounts because they resist clean narrative form

When coherence bias IS present:
- Coherence is treated as evidence of truth
- Loose ends are resolved without adequate evidence
- Contradictions are smoothed away
- Messy complexity is rejected as unsatisfying
- Accuracy is sacrificed for a cleaner account

When no coherence bias:
- Messiness is tolerated when evidence is messy
- Loose ends remain open when unresolved
- Contradictions are preserved and investigated
- Complexity is included where warranted
- Accuracy is prioritized over narrative satisfaction

Output JSON with: coherence_bias_detected (bool), severity (none/mild/moderate/severe), loose_end_intolerance (what loose ends are not tolerated), narrative_smoothing (what complexity is smoothed), complexity_rejection (what complexity is rejected), recommendation (no_coherence_bias/mild_messiness_tolerance/significant_evidence_priority/major_truth_over_coherence/emergency_complete_narrative_reconstruction)."""

EPISTEMIC_NARRATIVE_CONSTRUCTION_COHERENCE_BIAS_PROMPT = """Detect epistemic narrative construction coherence bias:

Coherence over accuracy: {coherence_over_accuracy}
Loose-end intolerance: {loose_end_intolerance}
Narrative smoothing: {narrative_smoothing}
Complexity rejection: {complexity_rejection}
Domain: {domain}
Context: {context}

Is a coherent narrative being preferred over an accurate but messy account? Return ONLY valid JSON."""


class EpistemicNarrativeConstructionCoherenceBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        coherence_over_accuracy: str,
        *,
        loose_end_intolerance: str = "",
        narrative_smoothing: str = "",
        complexity_rejection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CONSTRUCTION_COHERENCE_BIAS_PROMPT.format(
                coherence_over_accuracy=coherence_over_accuracy,
                loose_end_intolerance=loose_end_intolerance or "Not specified",
                narrative_smoothing=narrative_smoothing or "Not specified",
                complexity_rejection=complexity_rejection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CONSTRUCTION_COHERENCE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "coherence_over_accuracy": coherence_over_accuracy[:200],
            "coherence_bias_detected": data.get("coherence_bias_detected", False),
            "severity": data.get("severity", ""),
            "loose_end_intolerance": data.get("loose_end_intolerance", ""),
            "narrative_smoothing": data.get("narrative_smoothing", ""),
            "complexity_rejection": data.get("complexity_rejection", ""),
            "recommendation": data.get("recommendation", ""),
        }

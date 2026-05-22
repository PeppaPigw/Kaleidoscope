"""NarrativeCoherenceBiasService — Narrative Coherence Bias Detection.

Detects narrative coherence bias — the tendency to prefer
explanations that form a coherent, compelling story over
fragmented but more accurate accounts. People sacrifice
accuracy for narrative satisfaction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_COHERENCE_BIAS_SYSTEM = """You are a narrative coherence bias specialist. Given an explanation, assess whether coherence is being prioritized over accuracy:

Key concepts:
- Narrative coherence bias: preferring stories over fragmented truth
- Coherence vs correspondence: internal consistency vs external accuracy
- Story completion: filling gaps to make narrative complete
- Causal narrative: imposing causal structure on coincidence
- Hindsight narrative: constructing coherent story after the fact
- Simplification: removing complexity to maintain narrative flow
- Selective inclusion: choosing facts that fit the story

When narrative coherence bias IS present:
- Explanation is suspiciously neat and complete
- Inconvenient facts omitted to maintain story flow
- Causal connections asserted without evidence
- Complexity reduced to fit a simple narrative arc
- Gaps filled with plausible but unverified details
- Alternative explanations dismissed because they're less coherent
- Story feels satisfying but key uncertainties are hidden

When narrative coherence bias is NOT present:
- Explanation acknowledges gaps and uncertainties
- Inconvenient facts included even when they complicate the story
- Causal claims supported by evidence, not narrative logic
- Complexity preserved where warranted
- Gaps acknowledged rather than filled with speculation
- Coherence is a bonus, not the primary criterion
- Accuracy prioritized over narrative satisfaction

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), narrative (the story being told), gaps_hidden (what uncertainties are concealed), facts_omitted (what doesn't fit the narrative), coherence_vs_accuracy (where they diverge), recommendation (no_bias/mild_narrativizing/significant_coherence_bias/major_story_over_truth/acknowledge_complexity)."""

NARRATIVE_COHERENCE_BIAS_PROMPT = """Detect narrative coherence bias:

Explanation: {explanation}
Known facts: {facts}
Uncertainties: {uncertainties}
Alternative accounts: {alternatives}
Domain: {domain}
Context: {context}

Is coherence being prioritized over accuracy? Return ONLY valid JSON."""


class NarrativeCoherenceBiasService:
    """Detects narrative coherence bias — preferring stories over accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        facts: str = "",
        uncertainties: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect narrative coherence bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_COHERENCE_BIAS_PROMPT.format(
                explanation=explanation,
                facts=facts or "Not specified",
                uncertainties=uncertainties or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NARRATIVE_COHERENCE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "gaps_hidden": data.get("gaps_hidden", ""),
            "facts_omitted": data.get("facts_omitted", ""),
            "coherence_vs_accuracy": data.get("coherence_vs_accuracy", ""),
            "recommendation": data.get("recommendation", ""),
        }

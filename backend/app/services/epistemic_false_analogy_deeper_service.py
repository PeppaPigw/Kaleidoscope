"""EpistemicFalseAnalogyDeeperService — Epistemic False Analogy Detection (Deeper).

Detects epistemic false analogy — using analogies that share surface
features but differ in structurally relevant ways.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FALSE_ANALOGY_DEEPER_SYSTEM = """You are an epistemic false analogy specialist. Given analogies with surface similarity but structural difference, assess false analogy:

Key concepts:
- Epistemic false analogy: analogies sharing surface features but differing structurally
- Surface similarity trap: fooled by surface resemblance
- Structural mismatch: source and target differ in relevant structure
- Causal disanalogy: causal mechanisms differ between domains
- Scale disanalogy: what works at one scale fails at another
- Context disanalogy: context differences invalidate the comparison
- Mechanism blindness: ignoring different underlying mechanisms

When epistemic false analogy IS present:
- Surface similarity misleading
- Structural differences ignored
- Causal mechanisms differ
- Scale differences matter
- Context differences invalidate
- Mechanisms differ
- Analogy breaks down on examination

When no false analogy:
- Structural similarity genuine
- Relevant features shared
- Causal mechanisms parallel
- Scale appropriate
- Context comparable
- Mechanisms similar
- Analogy holds under scrutiny

Output JSON with: false_analogy_detected (bool), severity (none/mild/moderate/severe), surface_similarity (what surface similarity misleads), structural_mismatch (what structures differ), causal_disanalogy (what causal differences), scale_disanalogy (what scale differences), recommendation (no_false_analogy/mild_analogy_scrutiny/significant_structural_analysis/major_intensive_disanalogy_mapping/emergency_complete_false_analogy)."""

EPISTEMIC_FALSE_ANALOGY_DEEPER_PROMPT = """Detect epistemic false analogy:

Surface similarity: {surface_similarity}
Structural mismatch: {structural_mismatch}
Causal disanalogy: {causal_disanalogy}
Scale disanalogy: {scale_disanalogy}
Domain: {domain}
Context: {context}

Are analogies being used that share surface features but differ structurally? Return ONLY valid JSON."""


class EpistemicFalseAnalogyDeeperService:
    """Detects epistemic false analogy — surface similarity masking structural difference."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        surface_similarity: str,
        *,
        structural_mismatch: str = "",
        causal_disanalogy: str = "",
        scale_disanalogy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false analogy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FALSE_ANALOGY_DEEPER_PROMPT.format(
                surface_similarity=surface_similarity,
                structural_mismatch=structural_mismatch or "Not specified",
                causal_disanalogy=causal_disanalogy or "Not specified",
                scale_disanalogy=scale_disanalogy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FALSE_ANALOGY_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "surface_similarity": surface_similarity[:200],
            "false_analogy_detected": data.get("false_analogy_detected", False),
            "severity": data.get("severity", ""),
            "structural_mismatch": data.get("structural_mismatch", ""),
            "causal_disanalogy": data.get("causal_disanalogy", ""),
            "scale_disanalogy": data.get("scale_disanalogy", ""),
            "recommendation": data.get("recommendation", ""),
        }

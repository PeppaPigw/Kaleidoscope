"""EpistemicMeaningCrisisService — Epistemic Meaning Crisis Detection.

Detects epistemic meaning crisis — collapse of the frameworks that made
intellectual life feel meaningful, coherent, and worth pursuing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEANING_CRISIS_SYSTEM = """You are an epistemic meaning crisis specialist. Given intellectual meaning collapse, assess meaning crisis:

Key concepts:
- Epistemic meaning crisis: collapse of meaning-making frameworks
- Coherence loss: things no longer fit together
- Relevance failure: cannot determine what matters
- Significance collapse: nothing feels important
- Wisdom deficit: knowledge without understanding
- Participatory breakdown: cannot engage with ideas meaningfully
- Perspectival loss: cannot see from any stable viewpoint

When epistemic meaning crisis IS present:
- Meaning-making collapsed
- Things don't fit together
- Cannot determine what matters
- Nothing feels important
- Knowledge without understanding
- Cannot engage meaningfully
- No stable viewpoint

When no meaning crisis:
- Meaning-making intact
- Coherent worldview
- Clear priorities
- Things feel important
- Understanding present
- Meaningful engagement
- Stable perspective

Output JSON with: meaning_crisis_detected (bool), severity (none/mild/moderate/severe), coherence_loss (what not fitting), relevance_failure (what cannot determine), significance_collapse (what not important), wisdom_deficit (what without understanding), recommendation (no_meaning_crisis/mild_meaning_exploration/significant_meaning_therapy/major_intensive_reconstruction/emergency_complete_collapse)."""

EPISTEMIC_MEANING_CRISIS_PROMPT = """Detect epistemic meaning crisis:

Coherence loss: {coherence_loss}
Relevance failure: {relevance_failure}
Significance collapse: {significance_collapse}
Wisdom deficit: {wisdom_deficit}
Domain: {domain}
Context: {context}

Is there collapse of frameworks that made intellectual life feel meaningful? Return ONLY valid JSON."""


class EpistemicMeaningCrisisService:
    """Detects epistemic meaning crisis — collapse of meaning-making frameworks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        coherence_loss: str,
        *,
        relevance_failure: str = "",
        significance_collapse: str = "",
        wisdom_deficit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meaning crisis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEANING_CRISIS_PROMPT.format(
                coherence_loss=coherence_loss,
                relevance_failure=relevance_failure or "Not specified",
                significance_collapse=significance_collapse or "Not specified",
                wisdom_deficit=wisdom_deficit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEANING_CRISIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "coherence_loss": coherence_loss[:200],
            "meaning_crisis_detected": data.get("meaning_crisis_detected", False),
            "severity": data.get("severity", ""),
            "relevance_failure": data.get("relevance_failure", ""),
            "significance_collapse": data.get("significance_collapse", ""),
            "wisdom_deficit": data.get("wisdom_deficit", ""),
            "recommendation": data.get("recommendation", ""),
        }

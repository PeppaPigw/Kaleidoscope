"""EpistemicProbabilityThresholdService — Epistemic Probability Threshold Detection.

Detects epistemic probability threshold imposition — imposing arbitrary
probability thresholds for belief, creating false binary from continuous.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROBABILITY_THRESHOLD_SYSTEM = """You are an epistemic probability threshold specialist. Given arbitrary probability thresholds, assess threshold imposition:

Key concepts:
- Epistemic probability threshold: imposing arbitrary cutoffs for belief
- Arbitrary significance: arbitrary statistical significance thresholds
- Cliff edge thinking: treating threshold crossing as qualitative change
- Threshold gaming: gaming behavior around thresholds
- False precision in thresholds: false precision in where threshold is set
- Context-insensitive thresholds: same threshold regardless of stakes
- Threshold as binary: converting continuous probability to binary at threshold

When epistemic probability threshold IS present:
- Arbitrary thresholds imposed
- Significance arbitrary
- Cliff edges created
- Thresholds gamed
- False precision in cutoffs
- Context ignored in thresholds
- Continuous made binary

When no threshold imposition:
- Thresholds justified
- Significance contextual
- Gradual transitions acknowledged
- Thresholds robust
- Precision appropriate
- Context considered
- Continuous nature preserved

Output JSON with: probability_threshold_detected (bool), severity (none/mild/moderate/severe), arbitrary_significance (what arbitrary thresholds), cliff_edge_thinking (what cliff edges), threshold_gaming (what gaming), context_insensitive (what context ignored), recommendation (no_probability_threshold/mild_threshold_awareness/significant_threshold_justification/major_intensive_continuous_thinking/emergency_complete_probability_threshold)."""

EPISTEMIC_PROBABILITY_THRESHOLD_PROMPT = """Detect epistemic probability threshold imposition:

Arbitrary significance: {arbitrary_significance}
Cliff edge thinking: {cliff_edge_thinking}
Threshold gaming: {threshold_gaming}
Context insensitive: {context_insensitive}
Domain: {domain}
Context: {context}

Are arbitrary probability thresholds being imposed for belief? Return ONLY valid JSON."""


class EpistemicProbabilityThresholdService:
    """Detects epistemic probability threshold — arbitrary cutoffs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arbitrary_significance: str,
        *,
        cliff_edge_thinking: str = "",
        threshold_gaming: str = "",
        context_insensitive: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic probability threshold imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROBABILITY_THRESHOLD_PROMPT.format(
                arbitrary_significance=arbitrary_significance,
                cliff_edge_thinking=cliff_edge_thinking or "Not specified",
                threshold_gaming=threshold_gaming or "Not specified",
                context_insensitive=context_insensitive or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROBABILITY_THRESHOLD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arbitrary_significance": arbitrary_significance[:200],
            "probability_threshold_detected": data.get("probability_threshold_detected", False),
            "severity": data.get("severity", ""),
            "cliff_edge_thinking": data.get("cliff_edge_thinking", ""),
            "threshold_gaming": data.get("threshold_gaming", ""),
            "context_insensitive": data.get("context_insensitive", ""),
            "recommendation": data.get("recommendation", ""),
        }

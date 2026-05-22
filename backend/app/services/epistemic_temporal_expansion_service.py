"""EpistemicTemporalExpansionService — Epistemic Temporal Expansion Detection.

Detects epistemic temporal expansion — expanding recent events to seem
more significant than they are due to temporal proximity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_EXPANSION_SYSTEM = """You are an epistemic temporal expansion specialist. Given expanding recent events beyond significance, assess temporal expansion:

Key concepts:
- Epistemic temporal expansion: expanding recent events to seem more significant
- Recency inflation: inflating importance of recent events
- Present magnification: magnifying present moment beyond proportion
- Novelty overweighting: overweighting novel recent information
- Crisis inflation: inflating current crisis beyond historical proportion
- Immediacy bias: biasing toward immediate over historical
- Temporal myopia: seeing only the near and magnifying it

When epistemic temporal expansion IS present:
- Recent events expanded beyond significance
- Recency inflated
- Present magnified
- Novelty overweighted
- Crisis inflated
- Immediacy biased
- Temporal myopia active

When no temporal expansion:
- Recent events in proportion
- Recency balanced
- Present in context
- Novelty appropriately weighted
- Crisis in historical context
- Immediacy balanced with history
- Temporal vision broad

Output JSON with: temporal_expansion_detected (bool), severity (none/mild/moderate/severe), recency_inflation (what recent events inflated), present_magnification (what present magnified), novelty_overweighting (what novelty overweighted), crisis_inflation (what crisis inflated), recommendation (no_temporal_expansion/mild_historical_context/significant_proportion_recovery/major_intensive_temporal_calibration/emergency_complete_temporal_expansion)."""

EPISTEMIC_TEMPORAL_EXPANSION_PROMPT = """Detect epistemic temporal expansion:

Recency inflation: {recency_inflation}
Present magnification: {present_magnification}
Novelty overweighting: {novelty_overweighting}
Crisis inflation: {crisis_inflation}
Domain: {domain}
Context: {context}

Are recent events being expanded to seem more significant than they are? Return ONLY valid JSON."""


class EpistemicTemporalExpansionService:
    """Detects epistemic temporal expansion — expanding recent events beyond significance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        recency_inflation: str,
        *,
        present_magnification: str = "",
        novelty_overweighting: str = "",
        crisis_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal expansion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_EXPANSION_PROMPT.format(
                recency_inflation=recency_inflation,
                present_magnification=present_magnification or "Not specified",
                novelty_overweighting=novelty_overweighting or "Not specified",
                crisis_inflation=crisis_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_EXPANSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "recency_inflation": recency_inflation[:200],
            "temporal_expansion_detected": data.get("temporal_expansion_detected", False),
            "severity": data.get("severity", ""),
            "present_magnification": data.get("present_magnification", ""),
            "novelty_overweighting": data.get("novelty_overweighting", ""),
            "crisis_inflation": data.get("crisis_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }

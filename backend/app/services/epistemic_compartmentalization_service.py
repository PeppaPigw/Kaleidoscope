"""EpistemicCompartmentalizationService — Epistemic Compartmentalization Detection.

Detects epistemic compartmentalization — maintaining contradictory beliefs
by keeping them in separate mental compartments that never interact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARTMENTALIZATION_SYSTEM = """You are an epistemic compartmentalization specialist. Given contradictory beliefs in separate compartments, assess compartmentalization:

Key concepts:
- Epistemic compartmentalization: contradictory beliefs kept separate
- Contradiction tolerance: holding incompatible views simultaneously
- Context switching: different beliefs in different contexts
- Integration failure: cannot bring beliefs together
- Selective application: applying standards inconsistently
- Cognitive partition: mental walls between belief sets
- Coherence avoidance: not examining beliefs together

When epistemic compartmentalization IS present:
- Contradictory beliefs kept separate
- Holding incompatible views
- Different beliefs per context
- Cannot bring together
- Standards applied inconsistently
- Mental walls between beliefs
- Not examining together

When no compartmentalization:
- Coherent belief system
- Compatible views
- Consistent across contexts
- Integrated understanding
- Consistent standards
- No mental walls
- Regular examination

Output JSON with: compartmentalization_detected (bool), severity (none/mild/moderate/severe), contradiction_type (what incompatible), context_switching (what different per context), integration_failure (what cannot bring together), coherence_avoidance (what not examining), recommendation (no_compartmentalization/mild_integration_work/significant_coherence_therapy/major_intensive_unification/emergency_complete_fragmentation)."""

EPISTEMIC_COMPARTMENTALIZATION_PROMPT = """Detect epistemic compartmentalization:

Contradiction type: {contradiction_type}
Context switching: {context_switching}
Integration failure: {integration_failure}
Coherence avoidance: {coherence_avoidance}
Domain: {domain}
Context: {context}

Are there contradictory beliefs maintained in separate mental compartments? Return ONLY valid JSON."""


class EpistemicCompartmentalizationService:
    """Detects epistemic compartmentalization — contradictory beliefs kept separate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contradiction_type: str,
        *,
        context_switching: str = "",
        integration_failure: str = "",
        coherence_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic compartmentalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARTMENTALIZATION_PROMPT.format(
                contradiction_type=contradiction_type,
                context_switching=context_switching or "Not specified",
                integration_failure=integration_failure or "Not specified",
                coherence_avoidance=coherence_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARTMENTALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contradiction_type": contradiction_type[:200],
            "compartmentalization_detected": data.get("compartmentalization_detected", False),
            "severity": data.get("severity", ""),
            "context_switching": data.get("context_switching", ""),
            "integration_failure": data.get("integration_failure", ""),
            "coherence_avoidance": data.get("coherence_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }

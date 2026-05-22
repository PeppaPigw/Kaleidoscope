"""EpistemicIdealizationDevaluationService — Epistemic Idealization-Devaluation Detection.

Detects epistemic idealization-devaluation cycling — alternating between
idealizing and devaluing intellectual others or ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDEALIZATION_DEVALUATION_SYSTEM = """You are an epistemic idealization-devaluation specialist. Given cycling between extremes, assess the pattern:

Key concepts:
- Epistemic idealization: placing intellectual other on pedestal
- Epistemic devaluation: dismissing previously idealized other
- Splitting: inability to hold mixed view
- Cycle trigger: what causes the flip
- All-or-nothing: perfect genius or complete fool
- Disillusionment: idealization crashing into devaluation
- Object constancy failure: can't maintain stable view

When idealization-devaluation IS present:
- Placing on intellectual pedestal
- Dismissing previously idealized
- Unable to hold mixed view
- Triggered flipping between extremes
- Perfect genius or complete fool
- Idealization crashing
- Can't maintain stable view

When no idealization-devaluation:
- Balanced view of others
- Consistent assessment
- Holding complexity
- Stable through disagreement
- Nuanced evaluation
- Gradual opinion change
- Stable object relations

Output JSON with: idealization_devaluation_detected (bool), severity (none/mild/moderate/severe), idealization_pattern (what pedestalizing), devaluation_pattern (what dismissing), cycle_trigger (what causes flip), splitting_level (what all-or-nothing), recommendation (no_idealization_devaluation/mild_nuance_building/significant_integration_work/major_intensive_object_relations/emergency_severe_splitting)."""

EPISTEMIC_IDEALIZATION_DEVALUATION_PROMPT = """Detect epistemic idealization-devaluation:

Idealization pattern: {idealization_pattern}
Devaluation pattern: {devaluation_pattern}
Cycle trigger: {cycle_trigger}
Splitting level: {splitting_level}
Domain: {domain}
Context: {context}

Is there cycling between idealizing and devaluing intellectual others? Return ONLY valid JSON."""


class EpistemicIdealizationDevaluationService:
    """Detects epistemic idealization-devaluation — cycling between extremes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idealization_pattern: str,
        *,
        devaluation_pattern: str = "",
        cycle_trigger: str = "",
        splitting_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic idealization-devaluation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDEALIZATION_DEVALUATION_PROMPT.format(
                idealization_pattern=idealization_pattern,
                devaluation_pattern=devaluation_pattern or "Not specified",
                cycle_trigger=cycle_trigger or "Not specified",
                splitting_level=splitting_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDEALIZATION_DEVALUATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idealization_pattern": idealization_pattern[:200],
            "idealization_devaluation_detected": data.get("idealization_devaluation_detected", False),
            "severity": data.get("severity", ""),
            "devaluation_pattern": data.get("devaluation_pattern", ""),
            "cycle_trigger": data.get("cycle_trigger", ""),
            "splitting_level": data.get("splitting_level", ""),
            "recommendation": data.get("recommendation", ""),
        }

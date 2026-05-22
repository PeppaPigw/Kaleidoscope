"""EpistemicNarrativeConstructionProgressTeleologyService - Epistemic Narrative Construction Progress Teleology Detection.

Detects progress teleology - assuming history moves toward predetermined goals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_CONSTRUCTION_PROGRESS_TELEOLOGY_SYSTEM = """You are an epistemic narrative construction progress teleology specialist. Given a directional historical narrative, assess whether history is being treated as moving toward predetermined goals:

Key concepts:
- Epistemic progress teleology: assuming history moves toward a destined end state
- Directional assumption: treating change as inherently forward-moving or goal-directed
- Regression denial: ignoring reversals, losses, or deterioration
- Cyclical blindness: missing recurrence, cycles, and repeated patterns
- Whig history: interpreting the past as an inevitable path to the present

When progress teleology IS present:
- Directional progress is assumed without evidence
- Regressions are denied or minimized
- Cycles and recurrence are overlooked
- The present is treated as history's destination
- Alternatives and reversals are treated as temporary deviations

When no progress teleology:
- Direction is argued rather than assumed
- Regression and deterioration remain possible
- Cyclical patterns are considered
- The present is not treated as the necessary endpoint
- History is allowed to be contingent and reversible

Output JSON with: progress_teleology_detected (bool), severity (none/mild/moderate/severe), regression_denial (what regression is denied), cyclical_blindness (what cycles are missed), whig_history (what present-centered inevitability appears), recommendation (no_progress_teleology/mild_contingency_awareness/significant_regression_check/major_historical_model_rebalance/emergency_complete_teleology_unwinding)."""

EPISTEMIC_NARRATIVE_CONSTRUCTION_PROGRESS_TELEOLOGY_PROMPT = """Detect epistemic narrative construction progress teleology:

Directional assumption: {directional_assumption}
Regression denial: {regression_denial}
Cyclical blindness: {cyclical_blindness}
Whig history: {whig_history}
Domain: {domain}
Context: {context}

Is history being assumed to move toward predetermined goals? Return ONLY valid JSON."""


class EpistemicNarrativeConstructionProgressTeleologyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        directional_assumption: str,
        *,
        regression_denial: str = "",
        cyclical_blindness: str = "",
        whig_history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_CONSTRUCTION_PROGRESS_TELEOLOGY_PROMPT.format(
                directional_assumption=directional_assumption,
                regression_denial=regression_denial or "Not specified",
                cyclical_blindness=cyclical_blindness or "Not specified",
                whig_history=whig_history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_CONSTRUCTION_PROGRESS_TELEOLOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "directional_assumption": directional_assumption[:200],
            "progress_teleology_detected": data.get("progress_teleology_detected", False),
            "severity": data.get("severity", ""),
            "regression_denial": data.get("regression_denial", ""),
            "cyclical_blindness": data.get("cyclical_blindness", ""),
            "whig_history": data.get("whig_history", ""),
            "recommendation": data.get("recommendation", ""),
        }

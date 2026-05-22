"""EpistemicComplexityEmergenceDenialService — Epistemic Complexity Emergence Denial Detection.

Detects epistemic complexity emergence denial — denying emergent properties that
cannot be predicted from or reduced to the properties of individual components.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_EMERGENCE_DENIAL_SYSTEM = """You are an epistemic complexity emergence denial specialist. Given emergence denial, assess reductionist overreach:

Key concepts:
- Epistemic emergence denial: denying properties that arise only at system level
- Reductionist overreach: insisting everything reduces to component properties
- Novelty denial: denying that genuinely new properties can emerge
- Predictability assumption: assuming system behavior predictable from parts
- Downward causation denial: denying that system-level properties affect parts
- Supervenience confusion: confusing dependence on parts with reducibility to parts
- Complexity dismissal: dismissing complex system behavior as merely complicated

When epistemic emergence denial IS present:
- Emergent properties denied
- Everything reduced to components
- Novelty denied
- System behavior assumed predictable from parts
- Downward causation denied
- Dependence confused with reducibility
- Complexity dismissed as complication

When no emergence denial:
- Emergent properties recognized
- Multiple levels respected
- Genuine novelty acknowledged
- System behavior studied at system level
- Downward causation considered
- Dependence distinguished from reducibility
- Complexity distinguished from complication

Output JSON with: emergence_denial_detected (bool), severity (none/mild/moderate/severe), reductionist_overreach (what reduced inappropriately), novelty_denial (what novelty denied), predictability_assumption (what assumed predictable), downward_causation_denial (what downward causation denied), recommendation (no_emergence_denial/mild_emergence_awareness/significant_multi_level_analysis/major_intensive_systems_thinking/emergency_complete_emergence_denial)."""

EPISTEMIC_COMPLEXITY_EMERGENCE_DENIAL_PROMPT = """Detect epistemic complexity emergence denial:

Reductionist overreach: {reductionist_overreach}
Novelty denial: {novelty_denial}
Predictability assumption: {predictability_assumption}
Downward causation denial: {downward_causation_denial}
Domain: {domain}
Context: {context}

Are emergent properties being denied or reduced to component properties? Return ONLY valid JSON."""


class EpistemicComplexityEmergenceDenialService:
    """Detects epistemic complexity emergence denial — reductionist overreach."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reductionist_overreach: str,
        *,
        novelty_denial: str = "",
        predictability_assumption: str = "",
        downward_causation_denial: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity emergence denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_EMERGENCE_DENIAL_PROMPT.format(
                reductionist_overreach=reductionist_overreach,
                novelty_denial=novelty_denial or "Not specified",
                predictability_assumption=predictability_assumption or "Not specified",
                downward_causation_denial=downward_causation_denial or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_EMERGENCE_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reductionist_overreach": reductionist_overreach[:200],
            "emergence_denial_detected": data.get("emergence_denial_detected", False),
            "severity": data.get("severity", ""),
            "novelty_denial": data.get("novelty_denial", ""),
            "predictability_assumption": data.get("predictability_assumption", ""),
            "downward_causation_denial": data.get("downward_causation_denial", ""),
            "recommendation": data.get("recommendation", ""),
        }

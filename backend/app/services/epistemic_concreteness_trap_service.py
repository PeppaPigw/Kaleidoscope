"""EpistemicConcretenessTrapService — Epistemic Concreteness Trap Detection.

Detects epistemic concreteness trap — being trapped in concrete details,
unable to see patterns or rise to appropriate abstraction levels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONCRETENESS_TRAP_SYSTEM = """You are an epistemic concreteness trap specialist. Given inability to rise above concrete details, assess concreteness trap:

Key concepts:
- Epistemic concreteness trap: trapped in concrete details, unable to see patterns
- Detail fixation: fixated on details at expense of big picture
- Pattern blindness: unable to see patterns across instances
- Generalization failure: failing to generalize from specific cases
- Tree-for-forest: seeing trees but not the forest
- Instance addiction: addicted to specific instances, unable to abstract
- Concrete literalism: taking everything literally, missing metaphor and analogy

When epistemic concreteness trap IS present:
- Trapped in concrete details
- Fixated on specifics
- Patterns not seen
- Generalization failing
- Forest missed for trees
- Addicted to instances
- Everything taken literally

When no concreteness trap:
- Details and patterns balanced
- Specifics inform generalities
- Patterns recognized
- Generalization appropriate
- Both trees and forest seen
- Instances inform abstractions
- Literal and figurative balanced

Output JSON with: concreteness_trap_detected (bool), severity (none/mild/moderate/severe), detail_fixation (what details fixated on), pattern_blindness (what patterns missed), generalization_failure (what failing to generalize), instance_addiction (what instances addicted to), recommendation (no_concreteness_trap/mild_pattern_practice/significant_abstraction_recovery/major_intensive_generalization/emergency_complete_concreteness_trap)."""

EPISTEMIC_CONCRETENESS_TRAP_PROMPT = """Detect epistemic concreteness trap:

Detail fixation: {detail_fixation}
Pattern blindness: {pattern_blindness}
Generalization failure: {generalization_failure}
Instance addiction: {instance_addiction}
Domain: {domain}
Context: {context}

Is there a concreteness trap — unable to see patterns above details? Return ONLY valid JSON."""


class EpistemicConcretenessTrapService:
    """Detects epistemic concreteness trap — stuck in details."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        detail_fixation: str,
        *,
        pattern_blindness: str = "",
        generalization_failure: str = "",
        instance_addiction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic concreteness trap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONCRETENESS_TRAP_PROMPT.format(
                detail_fixation=detail_fixation,
                pattern_blindness=pattern_blindness or "Not specified",
                generalization_failure=generalization_failure or "Not specified",
                instance_addiction=instance_addiction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONCRETENESS_TRAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "detail_fixation": detail_fixation[:200],
            "concreteness_trap_detected": data.get("concreteness_trap_detected", False),
            "severity": data.get("severity", ""),
            "pattern_blindness": data.get("pattern_blindness", ""),
            "generalization_failure": data.get("generalization_failure", ""),
            "instance_addiction": data.get("instance_addiction", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicNarcissisticMirroringService — Epistemic Narcissistic Mirroring Detection.

Detects epistemic narcissistic mirroring — needing others to reflect back
one's intellectual greatness and becoming distressed when they don't.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARCISSISTIC_MIRRORING_SYSTEM = """You are an epistemic narcissistic mirroring specialist. Given need for intellectual reflection, assess mirroring:

Key concepts:
- Epistemic narcissistic mirroring: needing others to reflect greatness
- Mirror hunger: desperate need for intellectual reflection
- Selfobject use: using others as mirrors not persons
- Empathic failure: distress when mirror doesn't reflect
- Twinship need: needing intellectual twin to validate
- Merger fantasy: wanting others to think exactly like self
- Fragmentation: falling apart without mirroring

When epistemic narcissistic mirroring IS present:
- Needing others to reflect greatness
- Desperate for intellectual reflection
- Using others as mirrors
- Distressed when not reflected
- Needing intellectual twin
- Wanting others to think like self
- Falling apart without mirroring

When no narcissistic mirroring:
- Self-sustaining intellectual identity
- Independent self-concept
- Relating to others as persons
- Tolerating difference
- Comfortable with uniqueness
- Accepting different thinking
- Stable without reflection

Output JSON with: narcissistic_mirroring_detected (bool), severity (none/mild/moderate/severe), mirror_hunger (what needing reflected), selfobject_use (what using others for), empathic_failure (what distress), fragmentation_risk (what falling apart), recommendation (no_narcissistic_mirroring/mild_self_sustaining_practice/significant_mirroring_reduction/major_intensive_selfobject_work/emergency_fragmentation)."""

EPISTEMIC_NARCISSISTIC_MIRRORING_PROMPT = """Detect epistemic narcissistic mirroring:

Mirror hunger: {mirror_hunger}
Selfobject use: {selfobject_use}
Empathic failure: {empathic_failure}
Fragmentation risk: {fragmentation_risk}
Domain: {domain}
Context: {context}

Is there need for others to reflect back intellectual greatness? Return ONLY valid JSON."""


class EpistemicNarcissisticMirroringService:
    """Detects epistemic narcissistic mirroring — needing intellectual reflection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        mirror_hunger: str,
        *,
        selfobject_use: str = "",
        empathic_failure: str = "",
        fragmentation_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narcissistic mirroring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARCISSISTIC_MIRRORING_PROMPT.format(
                mirror_hunger=mirror_hunger,
                selfobject_use=selfobject_use or "Not specified",
                empathic_failure=empathic_failure or "Not specified",
                fragmentation_risk=fragmentation_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARCISSISTIC_MIRRORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "mirror_hunger": mirror_hunger[:200],
            "narcissistic_mirroring_detected": data.get("narcissistic_mirroring_detected", False),
            "severity": data.get("severity", ""),
            "selfobject_use": data.get("selfobject_use", ""),
            "empathic_failure": data.get("empathic_failure", ""),
            "fragmentation_risk": data.get("fragmentation_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }

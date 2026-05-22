"""EpistemicCommunicationFailureService — Epistemic Communication Failure Detection.

Detects epistemic communication failure — inability to share complex
knowledge with others due to translation barriers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_FAILURE_SYSTEM = """You are an epistemic communication failure specialist. Given inability to share complex knowledge, assess communication failure:

Key concepts:
- Epistemic communication failure: inability to share complex knowledge
- Translation barrier: cannot convert understanding to words
- Vocabulary gap: lacking shared language for concepts
- Simplification loss: meaning lost when simplifying
- Audience mismatch: no audience for the complexity level
- Frustration cycle: repeated failed attempts to communicate
- Isolation through inexpressibility: ideas too complex to share

When epistemic communication failure IS present:
- Inability to share complex knowledge
- Cannot convert to words
- Lacking shared language
- Meaning lost when simplifying
- No audience for complexity
- Repeated failed attempts
- Ideas too complex to share

When no communication failure:
- Successfully sharing knowledge
- Converting understanding to words
- Shared language available
- Meaning preserved in translation
- Appropriate audience found
- Successful communication
- Ideas expressible

Output JSON with: communication_failure_detected (bool), severity (none/mild/moderate/severe), translation_barrier (what cannot convert), vocabulary_gap (what lacking language for), simplification_loss (what losing when simplifying), frustration_cycle (what repeatedly failing), recommendation (no_communication_failure/mild_translation_practice/significant_bridge_building/major_intensive_communication_work/emergency_severe_inexpressibility)."""

EPISTEMIC_COMMUNICATION_FAILURE_PROMPT = """Detect epistemic communication failure:

Translation barrier: {translation_barrier}
Vocabulary gap: {vocabulary_gap}
Simplification loss: {simplification_loss}
Frustration cycle: {frustration_cycle}
Domain: {domain}
Context: {context}

Is there inability to share complex knowledge with others? Return ONLY valid JSON."""


class EpistemicCommunicationFailureService:
    """Detects epistemic communication failure — inability to share complex knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        translation_barrier: str,
        *,
        vocabulary_gap: str = "",
        simplification_loss: str = "",
        frustration_cycle: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_FAILURE_PROMPT.format(
                translation_barrier=translation_barrier,
                vocabulary_gap=vocabulary_gap or "Not specified",
                simplification_loss=simplification_loss or "Not specified",
                frustration_cycle=frustration_cycle or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "translation_barrier": translation_barrier[:200],
            "communication_failure_detected": data.get("communication_failure_detected", False),
            "severity": data.get("severity", ""),
            "vocabulary_gap": data.get("vocabulary_gap", ""),
            "simplification_loss": data.get("simplification_loss", ""),
            "frustration_cycle": data.get("frustration_cycle", ""),
            "recommendation": data.get("recommendation", ""),
        }

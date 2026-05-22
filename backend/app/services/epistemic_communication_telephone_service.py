"""EpistemicCommunicationTelephoneService — Epistemic Communication Telephone Detection.

Detects epistemic communication telephone effect — telephone game distortion
where messages degrade through successive retelling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_TELEPHONE_SYSTEM = """You are an epistemic communication telephone specialist. Given telephone game distortion, assess communication degradation:

Key concepts:
- Epistemic communication telephone: messages degrading through retelling
- Serial distortion: each retelling introducing distortion
- Memorable mutation: messages mutating toward more memorable forms
- Narrative smoothing: rough edges smoothed in retelling
- Detail invention: details invented to fill gaps in retelling
- Emotional amplification: emotional content amplified through chain
- Coherence imposition: incoherent elements made coherent in retelling

When epistemic communication telephone IS present:
- Messages degrading through retelling
- Serial distortion accumulating
- Mutations toward memorable
- Rough edges smoothed
- Details invented
- Emotions amplified
- Coherence imposed

When no telephone effect:
- Messages preserved accurately
- Distortion minimal
- Content stable
- Details maintained
- Gaps acknowledged not filled
- Emotions calibrated
- Incoherence preserved when real

Output JSON with: communication_telephone_detected (bool), severity (none/mild/moderate/severe), serial_distortion (what serial distortion), memorable_mutation (what mutations toward memorable), detail_invention (what details invented), emotional_amplification (what emotions amplified), recommendation (no_telephone_effect/mild_source_checking/significant_chain_shortening/major_intensive_original_recovery/emergency_complete_telephone_effect)."""

EPISTEMIC_COMMUNICATION_TELEPHONE_PROMPT = """Detect epistemic communication telephone effect:

Serial distortion: {serial_distortion}
Memorable mutation: {memorable_mutation}
Detail invention: {detail_invention}
Emotional amplification: {emotional_amplification}
Domain: {domain}
Context: {context}

Are messages degrading through successive retelling like a telephone game? Return ONLY valid JSON."""


class EpistemicCommunicationTelephoneService:
    """Detects epistemic communication telephone — retelling degradation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        serial_distortion: str,
        *,
        memorable_mutation: str = "",
        detail_invention: str = "",
        emotional_amplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication telephone effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_TELEPHONE_PROMPT.format(
                serial_distortion=serial_distortion,
                memorable_mutation=memorable_mutation or "Not specified",
                detail_invention=detail_invention or "Not specified",
                emotional_amplification=emotional_amplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_TELEPHONE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "serial_distortion": serial_distortion[:200],
            "communication_telephone_detected": data.get("communication_telephone_detected", False),
            "severity": data.get("severity", ""),
            "memorable_mutation": data.get("memorable_mutation", ""),
            "detail_invention": data.get("detail_invention", ""),
            "emotional_amplification": data.get("emotional_amplification", ""),
            "recommendation": data.get("recommendation", ""),
        }

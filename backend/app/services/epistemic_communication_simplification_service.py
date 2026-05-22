"""EpistemicCommunicationSimplificationService — Epistemic Communication Simplification Detection.

Detects epistemic communication oversimplification — oversimplifying complex
ideas in communication, losing essential complexity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_SIMPLIFICATION_SYSTEM = """You are an epistemic communication simplification specialist. Given oversimplified communication, assess simplification:

Key concepts:
- Epistemic communication simplification: losing essential complexity in communication
- Nuance elimination: eliminating nuance for simplicity
- False clarity: achieving clarity by removing necessary complexity
- Soundbite reduction: reducing complex ideas to soundbites
- Binary simplification: reducing complex spectrums to binary
- Mechanism omission: omitting mechanisms for simplicity
- Caveat elimination: eliminating caveats and limitations

When epistemic communication simplification IS present:
- Essential complexity lost
- Nuance eliminated
- False clarity achieved
- Ideas reduced to soundbites
- Spectrums made binary
- Mechanisms omitted
- Caveats eliminated

When no oversimplification:
- Complexity preserved appropriately
- Nuance maintained
- Clarity genuine
- Ideas properly summarized
- Spectrums acknowledged
- Mechanisms included
- Caveats noted

Output JSON with: communication_simplification_detected (bool), severity (none/mild/moderate/severe), nuance_elimination (what nuance eliminated), false_clarity (what false clarity), soundbite_reduction (what reduced to soundbites), binary_simplification (what made binary), recommendation (no_simplification/mild_complexity_preservation/significant_nuance_restoration/major_intensive_complexity_recovery/emergency_complete_simplification)."""

EPISTEMIC_COMMUNICATION_SIMPLIFICATION_PROMPT = """Detect epistemic communication oversimplification:

Nuance elimination: {nuance_elimination}
False clarity: {false_clarity}
Soundbite reduction: {soundbite_reduction}
Binary simplification: {binary_simplification}
Domain: {domain}
Context: {context}

Are complex ideas being oversimplified in communication, losing essential complexity? Return ONLY valid JSON."""


class EpistemicCommunicationSimplificationService:
    """Detects epistemic communication simplification — complexity lost."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nuance_elimination: str,
        *,
        false_clarity: str = "",
        soundbite_reduction: str = "",
        binary_simplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic communication oversimplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_SIMPLIFICATION_PROMPT.format(
                nuance_elimination=nuance_elimination,
                false_clarity=false_clarity or "Not specified",
                soundbite_reduction=soundbite_reduction or "Not specified",
                binary_simplification=binary_simplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_SIMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nuance_elimination": nuance_elimination[:200],
            "communication_simplification_detected": data.get("communication_simplification_detected", False),
            "severity": data.get("severity", ""),
            "false_clarity": data.get("false_clarity", ""),
            "soundbite_reduction": data.get("soundbite_reduction", ""),
            "binary_simplification": data.get("binary_simplification", ""),
            "recommendation": data.get("recommendation", ""),
        }

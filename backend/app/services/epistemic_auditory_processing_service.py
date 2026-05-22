"""EpistemicAuditoryProcessingService — Epistemic Auditory Processing Detection.

Detects epistemic auditory processing disorder — signals reach the brain
but cannot be decoded into meaning, despite intact reception.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUDITORY_PROCESSING_SYSTEM = """You are an epistemic auditory processing specialist. Given signal decoding failure despite intact reception, assess APD:

Key concepts:
- Epistemic APD: signals received but not decoded into meaning
- Temporal processing: inability to process rapid sequences
- Dichotic listening: difficulty with competing inputs
- Auditory closure: inability to fill in missing parts
- Pattern recognition: failure to identify signal patterns
- Auditory memory: inability to retain decoded signals
- Environmental modification: changing input conditions

When epistemic APD IS present:
- Signals received but not decoded
- Rapid sequences not processed
- Competing inputs causing confusion
- Unable to fill in missing parts
- Pattern recognition failing
- Decoded signals not retained
- Input conditions need modification

When no APD:
- Signals decoded into meaning
- Rapid sequences processed
- Competing inputs managed
- Missing parts filled naturally
- Patterns recognized
- Decoded signals retained
- Normal input conditions sufficient

Output JSON with: apd_detected (bool), severity (none/mild/moderate/severe), processing_deficit (what decoding failure), temporal_processing (what sequence handling), competing_input_handling (what dichotic ability), pattern_recognition (what identification), recommendation (no_apd/mild_environmental_modification/significant_auditory_training/major_comprehensive_therapy/emergency_sudden_processing_loss)."""

EPISTEMIC_AUDITORY_PROCESSING_PROMPT = """Detect epistemic auditory processing disorder:

Processing deficit: {processing_deficit}
Temporal processing: {temporal_processing}
Competing input handling: {competing_input_handling}
Pattern recognition: {pattern_recognition}
Domain: {domain}
Context: {context}

Are intellectual signals reaching the brain but failing to be decoded into meaning? Return ONLY valid JSON."""


class EpistemicAuditoryProcessingService:
    """Detects epistemic APD — signals received but not decoded into meaning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        processing_deficit: str,
        *,
        temporal_processing: str = "",
        competing_input_handling: str = "",
        pattern_recognition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic auditory processing disorder."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUDITORY_PROCESSING_PROMPT.format(
                processing_deficit=processing_deficit,
                temporal_processing=temporal_processing or "Not specified",
                competing_input_handling=competing_input_handling or "Not specified",
                pattern_recognition=pattern_recognition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUDITORY_PROCESSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "processing_deficit": processing_deficit[:200],
            "apd_detected": data.get("apd_detected", False),
            "severity": data.get("severity", ""),
            "temporal_processing": data.get("temporal_processing", ""),
            "competing_input_handling": data.get("competing_input_handling", ""),
            "pattern_recognition": data.get("pattern_recognition", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicTemporalCompressionFallacyService — Epistemic Temporal Compression Fallacy Detection.

Detects epistemic temporal compression fallacy — compressing long timelines
into seeming simultaneity, losing crucial temporal structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_COMPRESSION_FALLACY_SYSTEM = """You are an epistemic temporal compression fallacy specialist. Given compressed timelines losing structure, assess temporal compression:

Key concepts:
- Epistemic temporal compression: compressing long timelines into seeming simultaneity
- History flattening: flattening historical development into single moment
- Process erasure: erasing the process that produced an outcome
- Gradual change blindness: missing gradual changes by compressing timeline
- Simultaneity illusion: making sequential events seem simultaneous
- Development denial: denying the development time required
- Instant expectation: expecting instant results from long processes

When epistemic temporal compression IS present:
- Timelines compressed
- History flattened
- Process erased
- Gradual changes missed
- Sequential made simultaneous
- Development denied
- Instant results expected

When no temporal compression:
- Timelines preserved
- History respected
- Process acknowledged
- Gradual changes tracked
- Sequence maintained
- Development time honored
- Patience appropriate

Output JSON with: temporal_compression_detected (bool), severity (none/mild/moderate/severe), history_flattening (what history flattened), process_erasure (what process erased), gradual_change_blindness (what gradual changes missed), instant_expectation (what instant results expected), recommendation (no_temporal_compression/mild_timeline_awareness/significant_process_recovery/major_intensive_temporal_reconstruction/emergency_complete_temporal_compression)."""

EPISTEMIC_TEMPORAL_COMPRESSION_FALLACY_PROMPT = """Detect epistemic temporal compression fallacy:

History flattening: {history_flattening}
Process erasure: {process_erasure}
Gradual change blindness: {gradual_change_blindness}
Instant expectation: {instant_expectation}
Domain: {domain}
Context: {context}

Are long timelines being compressed losing crucial temporal structure? Return ONLY valid JSON."""


class EpistemicTemporalCompressionFallacyService:
    """Detects epistemic temporal compression — timeline flattening."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        history_flattening: str,
        *,
        process_erasure: str = "",
        gradual_change_blindness: str = "",
        instant_expectation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal compression fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_COMPRESSION_FALLACY_PROMPT.format(
                history_flattening=history_flattening,
                process_erasure=process_erasure or "Not specified",
                gradual_change_blindness=gradual_change_blindness or "Not specified",
                instant_expectation=instant_expectation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_COMPRESSION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "history_flattening": history_flattening[:200],
            "temporal_compression_detected": data.get("temporal_compression_detected", False),
            "severity": data.get("severity", ""),
            "process_erasure": data.get("process_erasure", ""),
            "gradual_change_blindness": data.get("gradual_change_blindness", ""),
            "instant_expectation": data.get("instant_expectation", ""),
            "recommendation": data.get("recommendation", ""),
        }

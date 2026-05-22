"""EpistemicTemporalCompressionService — Epistemic Temporal Compression Detection.

Detects epistemic temporal compression — compressing complex timelines
into oversimplified narratives that lose important nuance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_COMPRESSION_SYSTEM = """You are an epistemic temporal compression specialist. Given compressing timelines into oversimplified narratives, assess temporal compression:

Key concepts:
- Epistemic temporal compression: compressing complex timelines into oversimplified narratives
- History flattening: flattening complex history into simple story
- Process erasure: erasing the process and seeing only endpoints
- Gradual change blindness: missing gradual changes by compressing time
- Milestone fixation: fixating on milestones and missing what happened between
- Narrative shortcutting: shortcutting complex temporal narratives
- Complexity collapse: collapsing temporal complexity into simple before/after

When epistemic temporal compression IS present:
- Timelines compressed and oversimplified
- History flattened
- Process erased
- Gradual changes missed
- Milestones fixated on
- Narratives shortcut
- Complexity collapsed

When no temporal compression:
- Timelines appreciated in full
- History understood in complexity
- Process valued
- Gradual changes noticed
- Between-milestones valued
- Narratives complete
- Complexity preserved

Output JSON with: temporal_compression_detected (bool), severity (none/mild/moderate/severe), history_flattening (what history flattened), process_erasure (what process erased), gradual_change_blindness (what gradual changes missed), complexity_collapse (what complexity collapsed), recommendation (no_temporal_compression/mild_timeline_expansion/significant_process_recovery/major_intensive_temporal_restoration/emergency_complete_temporal_compression)."""

EPISTEMIC_TEMPORAL_COMPRESSION_PROMPT = """Detect epistemic temporal compression:

History flattening: {history_flattening}
Process erasure: {process_erasure}
Gradual change blindness: {gradual_change_blindness}
Complexity collapse: {complexity_collapse}
Domain: {domain}
Context: {context}

Are complex timelines being compressed into oversimplified narratives? Return ONLY valid JSON."""


class EpistemicTemporalCompressionService:
    """Detects epistemic temporal compression — compressing timelines."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        history_flattening: str,
        *,
        process_erasure: str = "",
        gradual_change_blindness: str = "",
        complexity_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal compression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_COMPRESSION_PROMPT.format(
                history_flattening=history_flattening,
                process_erasure=process_erasure or "Not specified",
                gradual_change_blindness=gradual_change_blindness or "Not specified",
                complexity_collapse=complexity_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_COMPRESSION_SYSTEM,
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
            "complexity_collapse": data.get("complexity_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMemoryReconstructionService — Epistemic Memory Reconstruction Detection.

Detects epistemic memory reconstruction — unconsciously reconstructing
memories to fit current beliefs and positions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_RECONSTRUCTION_SYSTEM = """You are an epistemic memory reconstruction specialist. Given unconsciously reconstructing memories, assess memory reconstruction:

Key concepts:
- Epistemic memory reconstruction: unconsciously reconstructing memories to fit beliefs
- Hindsight editing: editing memories with hindsight
- Belief-consistent revision: revising memories to be consistent with beliefs
- Narrative smoothing: smoothing memories into coherent narrative
- Position-confirming distortion: distorting memories to confirm position
- History rewriting: rewriting personal intellectual history
- Retroactive justification: creating memories that justify current position

When epistemic memory reconstruction IS present:
- Unconsciously reconstructing memories
- Editing memories with hindsight
- Revising for belief consistency
- Smoothing into narrative
- Distorting to confirm position
- Rewriting intellectual history
- Creating justifying memories

When no memory reconstruction:
- Accurate memory preservation
- Memories unchanged by hindsight
- Memories independent of beliefs
- Raw memories maintained
- Undistorted memories
- Honest intellectual history
- Genuine memories

Output JSON with: memory_reconstruction_detected (bool), severity (none/mild/moderate/severe), hindsight_editing (what memories edited with hindsight), belief_consistent_revision (what revised for consistency), narrative_smoothing (what smoothed into narrative), history_rewriting (what history rewritten), recommendation (no_memory_reconstruction/mild_accuracy_check/significant_memory_audit/major_intensive_honesty_practice/emergency_complete_memory_reconstruction)."""

EPISTEMIC_MEMORY_RECONSTRUCTION_PROMPT = """Detect epistemic memory reconstruction:

Hindsight editing: {hindsight_editing}
Belief consistent revision: {belief_consistent_revision}
Narrative smoothing: {narrative_smoothing}
History rewriting: {history_rewriting}
Domain: {domain}
Context: {context}

Is there unconsciously reconstructing memories to fit current beliefs? Return ONLY valid JSON."""


class EpistemicMemoryReconstructionService:
    """Detects epistemic memory reconstruction — reconstructing to fit beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hindsight_editing: str,
        *,
        belief_consistent_revision: str = "",
        narrative_smoothing: str = "",
        history_rewriting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory reconstruction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_RECONSTRUCTION_PROMPT.format(
                hindsight_editing=hindsight_editing,
                belief_consistent_revision=belief_consistent_revision or "Not specified",
                narrative_smoothing=narrative_smoothing or "Not specified",
                history_rewriting=history_rewriting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_RECONSTRUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hindsight_editing": hindsight_editing[:200],
            "memory_reconstruction_detected": data.get("memory_reconstruction_detected", False),
            "severity": data.get("severity", ""),
            "belief_consistent_revision": data.get("belief_consistent_revision", ""),
            "narrative_smoothing": data.get("narrative_smoothing", ""),
            "history_rewriting": data.get("history_rewriting", ""),
            "recommendation": data.get("recommendation", ""),
        }

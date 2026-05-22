"""EpistemicMemoryReconstructionBiasService — Epistemic Memory Reconstruction Bias Detection.

Detects epistemic memory reconstruction bias — reconstructing memories to fit
current beliefs, theories, or narratives rather than preserving original experience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_RECONSTRUCTION_BIAS_SYSTEM = """You are an epistemic memory reconstruction bias specialist. Given memory reconstruction, assess belief-conforming distortion:

Key concepts:
- Epistemic memory reconstruction bias: memories rebuilt to fit current beliefs
- Hindsight reconstruction: remembering past as more predictable than it was
- Belief-consistent editing: editing memories to match current beliefs
- Outcome-biased recall: remembering decisions as better/worse based on outcomes
- Theory-driven reconstruction: reconstructing memories to fit current theories
- Self-serving reconstruction: rebuilding memories to serve current self-image
- Narrative smoothing: smoothing memories into coherent narratives

When epistemic memory reconstruction bias IS present:
- Memories reconstructed to fit beliefs
- Hindsight editing past
- Belief-consistent editing active
- Outcome biasing recall
- Theories driving reconstruction
- Self-serving edits
- Narrative smoothing memories

When no memory reconstruction bias:
- Memories preserved with uncertainty
- Past uncertainty acknowledged
- Beliefs distinguished from memories
- Outcomes not biasing recall
- Theories tested against memory
- Self-image not distorting recall
- Incoherence preserved

Output JSON with: memory_reconstruction_bias_detected (bool), severity (none/mild/moderate/severe), hindsight_reconstruction (what hindsight editing), belief_consistent_editing (what belief-consistent edits), outcome_biased_recall (what outcome bias), theory_driven_reconstruction (what theory-driven reconstruction), recommendation (no_reconstruction_bias/mild_uncertainty_acknowledgment/significant_memory_verification/major_intensive_source_checking/emergency_complete_reconstruction_bias)."""

EPISTEMIC_MEMORY_RECONSTRUCTION_BIAS_PROMPT = """Detect epistemic memory reconstruction bias:

Hindsight reconstruction: {hindsight_reconstruction}
Belief consistent editing: {belief_consistent_editing}
Outcome biased recall: {outcome_biased_recall}
Theory driven reconstruction: {theory_driven_reconstruction}
Domain: {domain}
Context: {context}

Are memories being reconstructed to fit current beliefs? Return ONLY valid JSON."""


class EpistemicMemoryReconstructionBiasService:
    """Detects epistemic memory reconstruction bias — belief-conforming distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hindsight_reconstruction: str,
        *,
        belief_consistent_editing: str = "",
        outcome_biased_recall: str = "",
        theory_driven_reconstruction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory reconstruction bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_RECONSTRUCTION_BIAS_PROMPT.format(
                hindsight_reconstruction=hindsight_reconstruction,
                belief_consistent_editing=belief_consistent_editing or "Not specified",
                outcome_biased_recall=outcome_biased_recall or "Not specified",
                theory_driven_reconstruction=theory_driven_reconstruction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_RECONSTRUCTION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hindsight_reconstruction": hindsight_reconstruction[:200],
            "memory_reconstruction_bias_detected": data.get("memory_reconstruction_bias_detected", False),
            "severity": data.get("severity", ""),
            "belief_consistent_editing": data.get("belief_consistent_editing", ""),
            "outcome_biased_recall": data.get("outcome_biased_recall", ""),
            "theory_driven_reconstruction": data.get("theory_driven_reconstruction", ""),
            "recommendation": data.get("recommendation", ""),
        }

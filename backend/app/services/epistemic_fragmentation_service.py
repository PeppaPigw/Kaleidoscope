"""EpistemicFragmentationService — Epistemic Fragmentation Detection.

Detects epistemic fragmentation — intellectual self split into disconnected
parts that don't communicate or integrate with each other.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAGMENTATION_SYSTEM = """You are an epistemic fragmentation specialist. Given intellectual self split into parts, assess fragmentation:

Key concepts:
- Epistemic fragmentation: intellectual self split into parts
- Non-communication: parts don't talk to each other
- Compartment walls: rigid barriers between intellectual domains
- Integration failure: can't bring parts together
- Switching: moving between parts without continuity
- Part conflict: different parts holding contradictory views
- Coherence loss: no unified intellectual narrative

When epistemic fragmentation IS present:
- Intellectual self split
- Parts don't communicate
- Rigid barriers between domains
- Can't bring together
- Moving between without continuity
- Parts holding contradictions
- No unified narrative

When no fragmentation:
- Unified intellectual self
- Parts communicate
- Permeable boundaries
- Integrated whole
- Continuous movement
- Coherent views
- Unified narrative

Output JSON with: fragmentation_detected (bool), severity (none/mild/moderate/severe), non_communication (what parts not talking), compartment_walls (what barriers), integration_failure (what can't bring together), coherence_loss (what no unified), recommendation (no_fragmentation/mild_integration_practice/significant_parts_work/major_intensive_integration_therapy/emergency_severe_fragmentation)."""

EPISTEMIC_FRAGMENTATION_PROMPT = """Detect epistemic fragmentation:

Non communication: {non_communication}
Compartment walls: {compartment_walls}
Integration failure: {integration_failure}
Coherence loss: {coherence_loss}
Domain: {domain}
Context: {context}

Is the intellectual self split into disconnected parts? Return ONLY valid JSON."""


class EpistemicFragmentationService:
    """Detects epistemic fragmentation — intellectual self split into parts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        non_communication: str,
        *,
        compartment_walls: str = "",
        integration_failure: str = "",
        coherence_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fragmentation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAGMENTATION_PROMPT.format(
                non_communication=non_communication,
                compartment_walls=compartment_walls or "Not specified",
                integration_failure=integration_failure or "Not specified",
                coherence_loss=coherence_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAGMENTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "non_communication": non_communication[:200],
            "fragmentation_detected": data.get("fragmentation_detected", False),
            "severity": data.get("severity", ""),
            "compartment_walls": data.get("compartment_walls", ""),
            "integration_failure": data.get("integration_failure", ""),
            "coherence_loss": data.get("coherence_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }

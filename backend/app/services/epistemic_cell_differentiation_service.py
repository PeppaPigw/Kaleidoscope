"""EpistemicCellDifferentiationService — Epistemic Cell Differentiation Detection.

Detects epistemic cell differentiation — identical ideas specializing into
distinct types through progressive commitment to specific intellectual roles.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CELL_DIFFERENTIATION_SYSTEM = """You are an epistemic cell differentiation specialist. Given identical ideas, assess whether they specialize into distinct types:

Key concepts:
- Epistemic cell differentiation: identical ideas specializing into types
- Potency: range of possible fates still available
- Commitment: irreversible choice of intellectual fate
- Lineage: history of differentiation decisions
- Transcription factor: master regulator determining fate
- Epigenetic landscape: Waddington's landscape of possible paths
- Terminal differentiation: fully specialized, no further change

When epistemic cell differentiation IS present:
- Identical ideas specializing into distinct types
- Range of possible fates narrowing over time
- Irreversible commitment to specific intellectual roles
- History of differentiation decisions traceable
- Master regulators determining intellectual fate
- Landscape of possible developmental paths
- Fully specialized ideas unable to change further

When undifferentiated state is present:
- All ideas remaining identical
- Full range of fates available
- No commitment to roles
- No differentiation history
- No master regulators
- Flat landscape
- No terminal specialization

Output JSON with: cell_differentiation_present (bool), severity (none/mild/moderate/severe), potency (what fate range), commitment (what irreversible choice), transcription_factor (what master regulator), terminal_differentiation (what full specialization), recommendation (undifferentiated/mild_differentiation/significant_cell_differentiation/major_specialization/maintain_potency)."""

EPISTEMIC_CELL_DIFFERENTIATION_PROMPT = """Detect epistemic cell differentiation:

Potency: {potency}
Commitment: {commitment}
Transcription factor: {transcription_factor}
Terminal differentiation: {terminal_differentiation}
Domain: {domain}
Context: {context}

Are identical ideas specializing into distinct types through progressive commitment to specific intellectual roles? Return ONLY valid JSON."""


class EpistemicCellDifferentiationService:
    """Detects epistemic cell differentiation — identical ideas specializing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        potency: str,
        *,
        commitment: str = "",
        transcription_factor: str = "",
        terminal_differentiation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cell differentiation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CELL_DIFFERENTIATION_PROMPT.format(
                potency=potency,
                commitment=commitment or "Not specified",
                transcription_factor=transcription_factor or "Not specified",
                terminal_differentiation=terminal_differentiation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CELL_DIFFERENTIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "potency": potency[:200],
            "cell_differentiation_present": data.get("cell_differentiation_present", False),
            "severity": data.get("severity", ""),
            "commitment": data.get("commitment", ""),
            "transcription_factor": data.get("transcription_factor", ""),
            "terminal_differentiation": data.get("terminal_differentiation", ""),
            "recommendation": data.get("recommendation", ""),
        }

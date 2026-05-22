"""EpistemicNarrativeImpositionService — Epistemic Narrative Imposition Detection.

Detects epistemic narrative imposition — imposing narrative structure
on events that don't inherently have one.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_IMPOSITION_SYSTEM = """You are an epistemic narrative imposition specialist. Given imposing narrative on events, assess narrative imposition:

Key concepts:
- Epistemic narrative imposition: imposing narrative structure on non-narrative events
- Plot projection: projecting plot onto plotless events
- Causation fabrication: fabricating causal chains where none exist
- Arc imposition: imposing dramatic arcs on flat sequences
- Character assignment: assigning character roles to neutral actors
- Climax expectation: expecting climaxes in non-dramatic situations
- Resolution demand: demanding resolution where none is coming

When epistemic narrative imposition IS present:
- Imposing narrative on non-narrative events
- Projecting plot onto plotless
- Fabricating causal chains
- Imposing dramatic arcs
- Assigning character roles
- Expecting climaxes
- Demanding resolution

When no narrative imposition:
- Accepting non-narrative events
- Recognizing plotless sequences
- Acknowledging acausal events
- Accepting flat sequences
- Seeing neutral actors
- Accepting non-dramatic situations
- Comfortable without resolution

Output JSON with: narrative_imposition_detected (bool), severity (none/mild/moderate/severe), plot_projection (what plot projected onto), causation_fabrication (what causal chains fabricated), arc_imposition (what arcs imposed on), resolution_demand (what resolution demanded from), recommendation (no_narrative_imposition/mild_reality_acceptance/significant_non_narrative_tolerance/major_intensive_structure_release/emergency_complete_narrative_imposition)."""

EPISTEMIC_NARRATIVE_IMPOSITION_PROMPT = """Detect epistemic narrative imposition:

Plot projection: {plot_projection}
Causation fabrication: {causation_fabrication}
Arc imposition: {arc_imposition}
Resolution demand: {resolution_demand}
Domain: {domain}
Context: {context}

Is there imposing narrative structure on events that don't have one? Return ONLY valid JSON."""


class EpistemicNarrativeImpositionService:
    """Detects epistemic narrative imposition — imposing narrative on non-narrative events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        plot_projection: str,
        *,
        causation_fabrication: str = "",
        arc_imposition: str = "",
        resolution_demand: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_IMPOSITION_PROMPT.format(
                plot_projection=plot_projection,
                causation_fabrication=causation_fabrication or "Not specified",
                arc_imposition=arc_imposition or "Not specified",
                resolution_demand=resolution_demand or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_IMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "plot_projection": plot_projection[:200],
            "narrative_imposition_detected": data.get("narrative_imposition_detected", False),
            "severity": data.get("severity", ""),
            "causation_fabrication": data.get("causation_fabrication", ""),
            "arc_imposition": data.get("arc_imposition", ""),
            "resolution_demand": data.get("resolution_demand", ""),
            "recommendation": data.get("recommendation", ""),
        }

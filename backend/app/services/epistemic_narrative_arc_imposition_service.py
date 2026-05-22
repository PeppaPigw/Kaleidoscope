"""EpistemicNarrativeArcImpositionService — Epistemic Narrative Arc Imposition Detection.

Detects epistemic narrative arc imposition — imposing dramatic arcs
on random or chaotic events that have no inherent narrative structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_ARC_IMPOSITION_SYSTEM = """You are an epistemic narrative arc imposition specialist. Given dramatic arc imposition on random events, assess arc imposition:

Key concepts:
- Epistemic narrative arc imposition: imposing dramatic arcs on random/chaotic events
- Pattern imposition: imposing narrative patterns on patternless events
- Drama injection: injecting dramatic structure where none exists
- Rising action fabrication: fabricating rising action in random sequences
- Climax expectation: expecting climactic moments in ongoing processes
- Resolution demand: demanding resolution from open-ended situations
- Foreshadowing illusion: seeing foreshadowing in random prior events

When epistemic narrative arc imposition IS present:
- Dramatic arcs imposed on random events
- Patterns imposed on patternless sequences
- Drama injected artificially
- Rising action fabricated
- Climaxes expected inappropriately
- Resolution demanded from chaos
- Foreshadowing seen in randomness

When no arc imposition:
- Events seen as potentially random
- Patterns only identified when evidenced
- Drama not artificially injected
- Sequences accepted as non-linear
- No climax expectations imposed
- Open-endedness accepted
- Prior events not retrofitted as foreshadowing

Output JSON with: narrative_arc_imposition_detected (bool), severity (none/mild/moderate/severe), pattern_imposition (what patterns imposed), drama_injection (what drama injected), climax_expectation (what climax expected), resolution_demand (what resolution demanded), recommendation (no_narrative_arc_imposition/mild_randomness_acceptance/significant_chaos_tolerance/major_intensive_pattern_release/emergency_complete_arc_imposition)."""

EPISTEMIC_NARRATIVE_ARC_IMPOSITION_PROMPT = """Detect epistemic narrative arc imposition:

Pattern imposition: {pattern_imposition}
Drama injection: {drama_injection}
Climax expectation: {climax_expectation}
Resolution demand: {resolution_demand}
Domain: {domain}
Context: {context}

Are dramatic arcs being imposed on random or chaotic events? Return ONLY valid JSON."""


class EpistemicNarrativeArcImpositionService:
    """Detects epistemic narrative arc imposition — drama on chaos."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern_imposition: str,
        *,
        drama_injection: str = "",
        climax_expectation: str = "",
        resolution_demand: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative arc imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_ARC_IMPOSITION_PROMPT.format(
                pattern_imposition=pattern_imposition,
                drama_injection=drama_injection or "Not specified",
                climax_expectation=climax_expectation or "Not specified",
                resolution_demand=resolution_demand or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_ARC_IMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern_imposition": pattern_imposition[:200],
            "narrative_arc_imposition_detected": data.get("narrative_arc_imposition_detected", False),
            "severity": data.get("severity", ""),
            "drama_injection": data.get("drama_injection", ""),
            "climax_expectation": data.get("climax_expectation", ""),
            "resolution_demand": data.get("resolution_demand", ""),
            "recommendation": data.get("recommendation", ""),
        }

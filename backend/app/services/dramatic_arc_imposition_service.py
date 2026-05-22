"""DramaticArcImpositionService — Dramatic Arc Imposition Detection.

Detects dramatic arc imposition — forcing reality into narrative
structures (rising action, climax, resolution) when actual events
don't follow such patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DRAMATIC_ARC_IMPOSITION_SYSTEM = """You are a dramatic arc imposition specialist. Given a narrative, assess whether reality is being forced into dramatic story structures:

Key concepts:
- Dramatic arc: rising action, climax, falling action, resolution
- Narrative closure: forcing endings where situations are ongoing
- Crisis framing: presenting gradual change as sudden crisis
- Turning point mythology: identifying false turning points
- Resolution bias: needing stories to have clean endings
- Conflict escalation: imposing escalating conflict structure
- Denouement demand: requiring satisfying conclusions

When dramatic arc imposition IS present:
- Gradual processes presented as having dramatic turning points
- Ongoing situations given false resolution or closure
- Events forced into rising-action/climax/resolution structure
- Complexity reduced to hero-vs-villain conflict
- Ambiguous outcomes presented as clear victories or defeats
- Timing of events adjusted to fit narrative rhythm
- Messy reality cleaned up into satisfying story

When narrative structure is appropriate:
- Events genuinely have dramatic structure
- Turning points are real, not imposed
- Complexity preserved within narrative
- Ongoing nature of situations acknowledged
- Multiple interpretations of events offered
- Narrative structure flagged as interpretive frame
- Reality's messiness preserved

Output JSON with: imposition_present (bool), severity (none/mild/moderate/severe), narrative (what story is told), arc_imposed (what dramatic structure is forced), reality (what the actual pattern of events is), false_closure (what false resolution is created), recommendation (appropriate_narrative/mild_dramatization/significant_arc_imposition/major_reality_distortion/acknowledge_messiness)."""

DRAMATIC_ARC_IMPOSITION_PROMPT = """Detect dramatic arc imposition:

Narrative: {narrative}
Events: {events}
Structure imposed: {structure}
Actual pattern: {actual}
Domain: {domain}
Context: {context}

Is reality being forced into dramatic narrative structures? Return ONLY valid JSON."""


class DramaticArcImpositionService:
    """Detects dramatic arc imposition — forcing reality into story structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        events: str = "",
        structure: str = "",
        actual: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect dramatic arc imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DRAMATIC_ARC_IMPOSITION_PROMPT.format(
                narrative=narrative,
                events=events or "Not specified",
                structure=structure or "Not specified",
                actual=actual or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DRAMATIC_ARC_IMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "imposition_present": data.get("imposition_present", False),
            "severity": data.get("severity", ""),
            "arc_imposed": data.get("arc_imposed", ""),
            "reality": data.get("reality", ""),
            "false_closure": data.get("false_closure", ""),
            "recommendation": data.get("recommendation", ""),
        }

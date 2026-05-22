"""EpistemicNarrativePersonificationService — Epistemic Narrative Personification Detection.

Detects epistemic narrative personification — attributing systemic outcomes
to individual actors for narrative appeal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_PERSONIFICATION_SYSTEM = """You are an epistemic narrative personification specialist. Given narrative personification, assess false individual attribution:

Key concepts:
- Epistemic narrative personification: attributing systemic outcomes to individuals
- Great man narrative: attributing systemic changes to individual genius/villainy
- System blindness: ignoring systemic factors for individual narrative
- Agency inflation: inflating individual agency over structural forces
- Blame personification: blaming individuals for systemic failures
- Credit personification: crediting individuals for systemic successes
- Structural invisibility: making structural causes invisible through personification

When epistemic narrative personification IS present:
- Systemic outcomes attributed to individuals
- Great man narratives imposed
- Systemic factors ignored
- Individual agency inflated
- Blame personified
- Credit personified
- Structural causes invisible

When no narrative personification:
- Systemic factors acknowledged
- Individual and structural causes balanced
- Agency appropriately attributed
- Blame distributed accurately
- Credit distributed accurately
- Structural causes visible
- Complexity of causation preserved

Output JSON with: narrative_personification_detected (bool), severity (none/mild/moderate/severe), great_man_narrative (what great man narratives), system_blindness (what systems ignored), agency_inflation (what agency inflated), blame_personification (what blame personified), recommendation (no_narrative_personification/mild_systemic_acknowledgment/significant_structural_inclusion/major_intensive_system_analysis/emergency_complete_narrative_personification)."""

EPISTEMIC_NARRATIVE_PERSONIFICATION_PROMPT = """Detect epistemic narrative personification:

Great man narrative: {great_man_narrative}
System blindness: {system_blindness}
Agency inflation: {agency_inflation}
Blame personification: {blame_personification}
Domain: {domain}
Context: {context}

Are systemic outcomes being attributed to individual actors for narrative appeal? Return ONLY valid JSON."""


class EpistemicNarrativePersonificationService:
    """Detects epistemic narrative personification — false individual attribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        great_man_narrative: str,
        *,
        system_blindness: str = "",
        agency_inflation: str = "",
        blame_personification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative personification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_PERSONIFICATION_PROMPT.format(
                great_man_narrative=great_man_narrative,
                system_blindness=system_blindness or "Not specified",
                agency_inflation=agency_inflation or "Not specified",
                blame_personification=blame_personification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_PERSONIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "great_man_narrative": great_man_narrative[:200],
            "narrative_personification_detected": data.get("narrative_personification_detected", False),
            "severity": data.get("severity", ""),
            "system_blindness": data.get("system_blindness", ""),
            "agency_inflation": data.get("agency_inflation", ""),
            "blame_personification": data.get("blame_personification", ""),
            "recommendation": data.get("recommendation", ""),
        }

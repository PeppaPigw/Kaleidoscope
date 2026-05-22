"""EpistemicNarrativeProtagonistService — Epistemic Narrative Protagonist Bias Detection.

Detects epistemic narrative protagonist bias — casting oneself as the
protagonist of a story, distorting objectivity through self-centering.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_PROTAGONIST_SYSTEM = """You are an epistemic narrative protagonist bias specialist. Given self-casting as protagonist distorting objectivity, assess protagonist bias:

Key concepts:
- Epistemic narrative protagonist bias: casting oneself as protagonist distorting objectivity
- Self-centering: placing self at center of all narratives
- Hero framing: framing own role as heroic or central
- Perspective monopoly: monopolizing the narrative perspective
- Agency inflation: inflating own agency in events
- Victimhood narrative: casting self as victim when convenient
- Savior complex: casting self as the one who must save the situation

When epistemic narrative protagonist bias IS present:
- Self cast as protagonist
- Narratives self-centered
- Own role framed as heroic
- Perspective monopolized
- Own agency inflated
- Victimhood or savior narratives adopted
- Others reduced to supporting characters

When no protagonist bias:
- Multiple perspectives considered
- Own role seen proportionally
- Others given full agency
- Perspective shared
- Agency distributed accurately
- No hero/victim framing
- Others seen as full agents

Output JSON with: narrative_protagonist_detected (bool), severity (none/mild/moderate/severe), self_centering (how self-centered), hero_framing (what hero framing present), agency_inflation (what agency inflated), perspective_monopoly (how perspective monopolized), recommendation (no_narrative_protagonist/mild_decentering_practice/significant_perspective_sharing/major_intensive_agency_redistribution/emergency_complete_protagonist_bias)."""

EPISTEMIC_NARRATIVE_PROTAGONIST_PROMPT = """Detect epistemic narrative protagonist bias:

Self-centering: {self_centering}
Hero framing: {hero_framing}
Agency inflation: {agency_inflation}
Perspective monopoly: {perspective_monopoly}
Domain: {domain}
Context: {context}

Is there protagonist bias — self cast as central character distorting objectivity? Return ONLY valid JSON."""


class EpistemicNarrativeProtagonistService:
    """Detects epistemic narrative protagonist bias — self as hero."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_centering: str,
        *,
        hero_framing: str = "",
        agency_inflation: str = "",
        perspective_monopoly: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative protagonist bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_PROTAGONIST_PROMPT.format(
                self_centering=self_centering,
                hero_framing=hero_framing or "Not specified",
                agency_inflation=agency_inflation or "Not specified",
                perspective_monopoly=perspective_monopoly or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_PROTAGONIST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_centering": self_centering[:200],
            "narrative_protagonist_detected": data.get("narrative_protagonist_detected", False),
            "severity": data.get("severity", ""),
            "hero_framing": data.get("hero_framing", ""),
            "agency_inflation": data.get("agency_inflation", ""),
            "perspective_monopoly": data.get("perspective_monopoly", ""),
            "recommendation": data.get("recommendation", ""),
        }

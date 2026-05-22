"""EpistemicPrematureMasteryService — Epistemic Premature Mastery Detection.

Detects epistemic premature mastery — claiming mastery before genuine
understanding has been achieved.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREMATURE_MASTERY_SYSTEM = """You are an epistemic premature mastery specialist. Given claiming mastery prematurely, assess premature mastery:

Key concepts:
- Epistemic premature mastery: claiming mastery before genuine understanding
- Surface fluency: fluent with surface but lacking depth
- Jargon mastery: mastering jargon without understanding concepts
- Confidence without competence: confident beyond actual competence
- Teaching before learning: teaching others before fully learning
- Expertise performance: performing expertise without having it
- Depth illusion: illusion of depth from surface familiarity

When epistemic premature mastery IS present:
- Claiming mastery prematurely
- Fluent at surface lacking depth
- Mastering jargon not concepts
- Confident beyond competence
- Teaching before learning
- Performing expertise without having
- Illusion of depth from surface

When no premature mastery:
- Accurate mastery claims
- Depth matches fluency
- Understanding behind jargon
- Confidence matches competence
- Teaching from genuine knowledge
- Genuine expertise
- Real depth

Output JSON with: premature_mastery_detected (bool), severity (none/mild/moderate/severe), surface_fluency (what fluent at surface about), jargon_mastery (what jargon mastered without understanding), confidence_without_competence (what confident about beyond competence), depth_illusion (what illusion of depth about), recommendation (no_premature_mastery/mild_depth_check/significant_humility_practice/major_intensive_genuine_learning/emergency_complete_premature_mastery)."""

EPISTEMIC_PREMATURE_MASTERY_PROMPT = """Detect epistemic premature mastery:

Surface fluency: {surface_fluency}
Jargon mastery: {jargon_mastery}
Confidence without competence: {confidence_without_competence}
Depth illusion: {depth_illusion}
Domain: {domain}
Context: {context}

Is there claiming mastery before genuine understanding? Return ONLY valid JSON."""


class EpistemicPrematureMasteryService:
    """Detects epistemic premature mastery — claiming mastery prematurely."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        surface_fluency: str,
        *,
        jargon_mastery: str = "",
        confidence_without_competence: str = "",
        depth_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic premature mastery."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREMATURE_MASTERY_PROMPT.format(
                surface_fluency=surface_fluency,
                jargon_mastery=jargon_mastery or "Not specified",
                confidence_without_competence=confidence_without_competence or "Not specified",
                depth_illusion=depth_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREMATURE_MASTERY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "surface_fluency": surface_fluency[:200],
            "premature_mastery_detected": data.get("premature_mastery_detected", False),
            "severity": data.get("severity", ""),
            "jargon_mastery": data.get("jargon_mastery", ""),
            "confidence_without_competence": data.get("confidence_without_competence", ""),
            "depth_illusion": data.get("depth_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

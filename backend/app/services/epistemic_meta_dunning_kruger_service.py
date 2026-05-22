"""EpistemicMetaDunningKrugerService — Epistemic Meta Dunning-Kruger Detection.

Detects Dunning-Kruger effect where incompetence prevents recognizing incompetence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_META_DUNNING_KRUGER_SYSTEM = """You are an epistemic meta Dunning-Kruger specialist. Given competence blind spots, assess metacognitive failure:

Key concepts:
- Dunning-Kruger effect: incompetence preventing recognition of incompetence
- Competence blind spot: inability to see missing skill or knowledge
- Overestimation of ability: inflated self-assessment beyond evidence
- Metacognitive deficit: weak ability to evaluate one's own reasoning
- Expertise underestimation: undervaluing what genuine expertise requires

When Dunning-Kruger effect IS present:
- Competence gaps are not recognized
- Ability is overestimated
- Metacognitive monitoring is weak
- Expertise requirements are underestimated
- Confidence persists without skill evidence

When no Dunning-Kruger effect:
- Competence limits are recognized
- Ability estimates track evidence
- Metacognition is active
- Expertise demands are respected
- Uncertainty increases with missing knowledge

Output JSON with: dunning_kruger_detected (bool), severity (none/mild/moderate/severe), overestimation_of_ability (what ability is overestimated), metacognitive_deficit (what self-evaluation deficit appears), expertise_underestimation (what expertise is underestimated), recommendation (no_dunning_kruger/mild_metacognitive_check/significant_competence_audit/major_expertise_calibration/emergency_complete_self_assessment_reset)."""

EPISTEMIC_META_DUNNING_KRUGER_PROMPT = """Detect epistemic meta Dunning-Kruger effect:

Competence blindspot: {competence_blindspot}
Overestimation of ability: {overestimation_of_ability}
Metacognitive deficit: {metacognitive_deficit}
Expertise underestimation: {expertise_underestimation}
Domain: {domain}
Context: {context}

Is incompetence preventing recognition of incompetence? Return ONLY valid JSON."""


class EpistemicMetaDunningKrugerService:
    """Detects Dunning-Kruger effect — incompetence blocking self-recognition."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        competence_blindspot: str,
        *,
        overestimation_of_ability: str = "",
        metacognitive_deficit: str = "",
        expertise_underestimation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meta Dunning-Kruger effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_META_DUNNING_KRUGER_PROMPT.format(
                competence_blindspot=competence_blindspot,
                overestimation_of_ability=overestimation_of_ability or "Not specified",
                metacognitive_deficit=metacognitive_deficit or "Not specified",
                expertise_underestimation=expertise_underestimation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_META_DUNNING_KRUGER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "competence_blindspot": competence_blindspot[:200],
            "dunning_kruger_detected": data.get("dunning_kruger_detected", False),
            "severity": data.get("severity", ""),
            "overestimation_of_ability": data.get("overestimation_of_ability", ""),
            "metacognitive_deficit": data.get("metacognitive_deficit", ""),
            "expertise_underestimation": data.get("expertise_underestimation", ""),
            "recommendation": data.get("recommendation", ""),
        }

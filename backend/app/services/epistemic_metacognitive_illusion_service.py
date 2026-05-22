"""EpistemicMetacognitiveIllusionService — Epistemic Metacognitive Illusion Detection.

Detects epistemic metacognitive illusion — illusions about one's own
cognitive abilities creating false confidence in thinking quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METACOGNITIVE_ILLUSION_SYSTEM = """You are an epistemic metacognitive illusion specialist. Given illusions about own cognitive abilities, assess metacognitive illusion:

Key concepts:
- Epistemic metacognitive illusion: illusions about own cognitive abilities
- Competence illusion: illusion of greater competence than actual
- Objectivity illusion: illusion of being more objective than one is
- Rationality illusion: illusion of being more rational than one is
- Awareness illusion: illusion of greater self-awareness than actual
- Control illusion: illusion of more cognitive control than actual
- Clarity illusion: illusion of clearer thinking than actual

When epistemic metacognitive illusion IS present:
- Illusions about abilities active
- Competence overestimated
- Objectivity overestimated
- Rationality overestimated
- Awareness overestimated
- Control overestimated
- Clarity overestimated

When no metacognitive illusion:
- Abilities accurately assessed
- Competence calibrated
- Objectivity realistically assessed
- Rationality honestly evaluated
- Awareness accurately gauged
- Control realistically assessed
- Clarity honestly evaluated

Output JSON with: metacognitive_illusion_detected (bool), severity (none/mild/moderate/severe), competence_illusion (what competence overestimated about), objectivity_illusion (what objectivity overestimated about), rationality_illusion (what rationality overestimated about), clarity_illusion (what clarity overestimated about), recommendation (no_metacognitive_illusion/mild_calibration_practice/significant_reality_testing/major_intensive_illusion_dissolution/emergency_complete_metacognitive_illusion)."""

EPISTEMIC_METACOGNITIVE_ILLUSION_PROMPT = """Detect epistemic metacognitive illusion:

Competence illusion: {competence_illusion}
Objectivity illusion: {objectivity_illusion}
Rationality illusion: {rationality_illusion}
Clarity illusion: {clarity_illusion}
Domain: {domain}
Context: {context}

Are there illusions about own cognitive abilities? Return ONLY valid JSON."""


class EpistemicMetacognitiveIllusionService:
    """Detects epistemic metacognitive illusion — illusions about own abilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        competence_illusion: str,
        *,
        objectivity_illusion: str = "",
        rationality_illusion: str = "",
        clarity_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metacognitive illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METACOGNITIVE_ILLUSION_PROMPT.format(
                competence_illusion=competence_illusion,
                objectivity_illusion=objectivity_illusion or "Not specified",
                rationality_illusion=rationality_illusion or "Not specified",
                clarity_illusion=clarity_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METACOGNITIVE_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "competence_illusion": competence_illusion[:200],
            "metacognitive_illusion_detected": data.get("metacognitive_illusion_detected", False),
            "severity": data.get("severity", ""),
            "objectivity_illusion": data.get("objectivity_illusion", ""),
            "rationality_illusion": data.get("rationality_illusion", ""),
            "clarity_illusion": data.get("clarity_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }

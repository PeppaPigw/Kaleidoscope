"""EpistemicConjunctionProbabilityService — Epistemic Conjunction Probability Detection.

Detects epistemic conjunction probability errors — violating the conjunction
rule where P(A&B) is judged greater than P(A) alone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONJUNCTION_PROBABILITY_SYSTEM = """You are an epistemic conjunction probability specialist. Given conjunction rule violations, assess conjunction probability errors:

Key concepts:
- Epistemic conjunction probability error: judging P(A&B) > P(A)
- Representativeness trap: conjunction seems more representative
- Narrative coherence bias: conjunction tells better story
- Detail addition illusion: adding detail seems to increase probability
- Scenario specificity: specific scenarios seem more likely than general
- Conjunction as explanation: conjunction provides explanation making it seem likely
- Subset-superset confusion: confusing subset probability with superset

When epistemic conjunction probability error IS present:
- Conjunction judged more likely than component
- Representativeness driving judgment
- Narrative coherence inflating probability
- Detail addition increasing perceived likelihood
- Specific scenarios preferred over general
- Explanatory conjunction overvalued
- Subset-superset confused

When no conjunction error:
- Conjunction correctly bounded by components
- Representativeness not dominating
- Narrative not inflating probability
- Detail recognized as constraining
- General correctly more likely than specific
- Explanation not inflating probability
- Subset-superset correctly related

Output JSON with: conjunction_probability_error_detected (bool), severity (none/mild/moderate/severe), representativeness_trap (what representativeness driving), narrative_coherence_bias (what narrative inflating), detail_addition_illusion (what detail adding), scenario_specificity (what specific preferred), recommendation (no_conjunction_error/mild_probability_awareness/significant_conjunction_checking/major_intensive_probability_training/emergency_complete_conjunction_error)."""

EPISTEMIC_CONJUNCTION_PROBABILITY_PROMPT = """Detect epistemic conjunction probability error:

Representativeness trap: {representativeness_trap}
Narrative coherence bias: {narrative_coherence_bias}
Detail addition illusion: {detail_addition_illusion}
Scenario specificity: {scenario_specificity}
Domain: {domain}
Context: {context}

Is the conjunction rule being violated in probability judgments? Return ONLY valid JSON."""


class EpistemicConjunctionProbabilityService:
    """Detects epistemic conjunction probability error — P(A&B) > P(A)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        representativeness_trap: str,
        *,
        narrative_coherence_bias: str = "",
        detail_addition_illusion: str = "",
        scenario_specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conjunction probability error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONJUNCTION_PROBABILITY_PROMPT.format(
                representativeness_trap=representativeness_trap,
                narrative_coherence_bias=narrative_coherence_bias or "Not specified",
                detail_addition_illusion=detail_addition_illusion or "Not specified",
                scenario_specificity=scenario_specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONJUNCTION_PROBABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "representativeness_trap": representativeness_trap[:200],
            "conjunction_probability_error_detected": data.get("conjunction_probability_error_detected", False),
            "severity": data.get("severity", ""),
            "narrative_coherence_bias": data.get("narrative_coherence_bias", ""),
            "detail_addition_illusion": data.get("detail_addition_illusion", ""),
            "scenario_specificity": data.get("scenario_specificity", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""ConjunctionFallacyService — Conjunction & Disjunction Fallacy Detection.

Detects when probability judgments violate basic rules:
- Conjunction fallacy: P(A and B) judged > P(A) alone
- Disjunction fallacy: P(A or B) judged < P(A) alone
- Narrative coherence mistaken for probability
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONJUNCTION_SYSTEM = """You are a probability fallacy specialist. Given a probability judgment, assess whether it commits conjunction or disjunction fallacy:
- Is a more specific/detailed scenario being judged as more likely than a general one?
- Is narrative coherence being confused with probability?
- Does adding detail make something seem more likely (when it mathematically can't)?
- Is the representativeness heuristic overriding probability rules?

Output JSON with: fallacy_present (bool), fallacy_type (conjunction/disjunction/representativeness/none), severity (none/mild/moderate/severe), specific_claim (the more detailed claim), general_claim (the less detailed but more probable claim), probability_relationship (specific_less_than_general/correctly_assessed), narrative_coherence_score (0-1, how good a story the specific claim makes), actual_probability_order (which is actually more likely), representativeness_trap (what makes the specific claim feel more likely), debiasing (how to think about this correctly), base_rate_relevant (the relevant base rate being ignored), correct_reasoning (step-by-step correct probabilistic reasoning)."""

CONJUNCTION_PROMPT = """Detect probability fallacies:

Judgment: {judgment}
Options considered: {options}
Domain: {domain}
Context: {context}

Is there a conjunction or disjunction fallacy? Return ONLY valid JSON."""


class ConjunctionFallacyService:
    """Detects conjunction and disjunction fallacies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        options: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect conjunction/disjunction fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONJUNCTION_PROMPT.format(
                judgment=judgment,
                options=options or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONJUNCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "fallacy_present": data.get("fallacy_present", False),
            "fallacy_type": data.get("fallacy_type", ""),
            "severity": data.get("severity", ""),
            "specific_claim": data.get("specific_claim", ""),
            "general_claim": data.get("general_claim", ""),
            "probability_relationship": data.get("probability_relationship", ""),
            "narrative_coherence_score": data.get("narrative_coherence_score", 0),
            "actual_probability_order": data.get("actual_probability_order", ""),
            "representativeness_trap": data.get("representativeness_trap", ""),
            "debiasing": data.get("debiasing", ""),
            "base_rate_relevant": data.get("base_rate_relevant", ""),
            "correct_reasoning": data.get("correct_reasoning", ""),
        }

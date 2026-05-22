"""IntellectualComfortSeekingService — Intellectual Comfort Seeking Detection.

Detects intellectual comfort seeking — seeking intellectually comfortable
conclusions over accurate ones, where cognitive ease is prioritized
over truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_COMFORT_SEEKING_SYSTEM = """You are an intellectual comfort seeking specialist. Given a reasoning process, assess whether comfort is being prioritized over accuracy:

Key concepts:
- Intellectual comfort seeking: preferring comfortable over accurate
- Cognitive ease preference: choosing easy conclusions over correct ones
- Discomfort avoidance: avoiding conclusions that cause discomfort
- Reassurance seeking: seeking reassuring over truthful answers
- Anxiety-driven reasoning: anxiety pushing toward comfortable conclusions
- Palatability over accuracy: choosing palatable over precise
- Emotional reasoning: feelings determining conclusions

When comfort seeking IS present:
- Comfortable conclusions preferred over accurate ones
- Discomforting evidence avoided or minimized
- Reassuring interpretations chosen without justification
- Cognitive ease prioritized over correctness
- Anxiety driving toward comfortable conclusions
- Palatability substituting for accuracy
- Feelings determining what is believed

When comfort alignment is appropriate:
- Comfortable conclusion also best supported by evidence
- Discomfort acknowledged but not driving conclusions
- Reassurance based on genuine evidence
- Ease of understanding not confused with truth
- Emotional responses noted but not determinative
- Comfort and accuracy happen to align
- Conclusions driven by evidence regardless of comfort

Output JSON with: comfort_seeking_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning is occurring), comfortable_conclusion (what comfortable conclusion is preferred), accurate_conclusion (what accurate conclusion is avoided), avoidance (what discomfort is avoided), recommendation (appropriate_reasoning/mild_comfort_preference/significant_comfort_seeking/major_accuracy_avoidance/prioritize_accuracy_over_comfort)."""

INTELLECTUAL_COMFORT_SEEKING_PROMPT = """Detect intellectual comfort seeking:

Reasoning: {reasoning}
Conclusion reached: {conclusion}
Uncomfortable alternative: {uncomfortable}
Evidence pattern: {evidence}
Domain: {domain}
Context: {context}

Is intellectual comfort being prioritized over accuracy? Return ONLY valid JSON."""


class IntellectualComfortSeekingService:
    """Detects intellectual comfort seeking — comfort prioritized over accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conclusion: str = "",
        uncomfortable: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual comfort seeking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_COMFORT_SEEKING_PROMPT.format(
                reasoning=reasoning,
                conclusion=conclusion or "Not specified",
                uncomfortable=uncomfortable or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_COMFORT_SEEKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "comfort_seeking_present": data.get("comfort_seeking_present", False),
            "severity": data.get("severity", ""),
            "comfortable_conclusion": data.get("comfortable_conclusion", ""),
            "accurate_conclusion": data.get("accurate_conclusion", ""),
            "avoidance": data.get("avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }

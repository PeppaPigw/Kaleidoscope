"""EuphemisticAbstractionService — Euphemistic Abstraction Detection.

Detects euphemistic abstraction — using abstract language to
distance from concrete harmful realities, making harmful things
sound neutral or even positive through abstraction.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EUPHEMISTIC_ABSTRACTION_SYSTEM = """You are a euphemistic abstraction specialist. Given language use, assess whether abstraction is being used to distance from harmful realities:

Key concepts:
- Euphemistic abstraction: abstract language hiding concrete harm
- Sanitizing language: making harmful things sound neutral
- Bureaucratic euphemism: administrative language hiding human cost
- Technical distancing: technical terms creating emotional distance
- Passive voice distancing: removing agency from harmful actions
- Nominalization: turning actions into abstract nouns
- Moral disengagement through language: words enabling harm

When euphemistic abstraction IS present:
- Abstract language hiding concrete harmful realities
- Technical or bureaucratic terms sanitizing harm
- Passive voice removing agency from harmful actions
- Nominalization turning harmful actions into neutral processes
- Language creating emotional distance from suffering
- Euphemisms making harmful policies sound benign
- Abstraction enabling moral disengagement

When abstract language is appropriate:
- Abstraction serves genuine analytical purpose
- Concrete realities acknowledged alongside abstractions
- Technical language used for precision, not distancing
- Agency preserved in descriptions of actions
- Emotional reality not hidden by language choices
- Abstraction level appropriate for context
- Language choices not serving to minimize harm

Output JSON with: abstraction_present (bool), severity (none/mild/moderate/severe), language (what language is used), concrete_reality (what concrete reality is hidden), distancing_mechanism (how language creates distance), who_benefits (who benefits from the abstraction), recommendation (appropriate_abstraction/mild_distancing/significant_euphemism/major_sanitization/use_concrete_language)."""

EUPHEMISTIC_ABSTRACTION_PROMPT = """Detect euphemistic abstraction:

Language: {language}
Topic: {topic}
Concrete reality: {reality}
Purpose: {purpose}
Domain: {domain}
Context: {context}

Is abstract language being used to distance from concrete harmful realities? Return ONLY valid JSON."""


class EuphemisticAbstractionService:
    """Detects euphemistic abstraction — abstract language hiding concrete harm."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        language: str,
        *,
        topic: str = "",
        reality: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect euphemistic abstraction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EUPHEMISTIC_ABSTRACTION_PROMPT.format(
                language=language,
                topic=topic or "Not specified",
                reality=reality or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EUPHEMISTIC_ABSTRACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "language": language[:200],
            "abstraction_present": data.get("abstraction_present", False),
            "severity": data.get("severity", ""),
            "concrete_reality": data.get("concrete_reality", ""),
            "distancing_mechanism": data.get("distancing_mechanism", ""),
            "who_benefits": data.get("who_benefits", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicTranslationBetrayalService — Epistemic Translation Betrayal Detection.

Detects epistemic translation betrayal — betraying meaning when
translating between frameworks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRANSLATION_BETRAYAL_SYSTEM = """You are an epistemic translation betrayal specialist. Given betraying meaning in translation, assess translation betrayal:

Key concepts:
- Epistemic translation betrayal: betraying meaning when translating frameworks
- Meaning distortion: distorting meaning when moving between contexts
- Framework violence: forcing ideas into incompatible frameworks
- Conceptual colonization: imposing one framework's concepts on another
- Translation loss denial: denying that translation loses meaning
- Interpretive violence: interpreting in ways that betray original meaning
- Context stripping: removing context that gives meaning

When epistemic translation betrayal IS present:
- Betraying meaning in translation
- Distorting when moving between contexts
- Forcing into incompatible frameworks
- Imposing one framework on another
- Denying translation loses meaning
- Interpreting to betray original
- Removing meaning-giving context

When no translation betrayal:
- Faithful translation
- Preserving meaning across contexts
- Respecting framework differences
- Acknowledging framework limits
- Honest about translation loss
- Faithful interpretation
- Preserving context

Output JSON with: translation_betrayal_detected (bool), severity (none/mild/moderate/severe), meaning_distortion (what distorting in translation), framework_violence (what forcing into incompatible), conceptual_colonization (what imposing on another), context_stripping (what removing context from), recommendation (no_translation_betrayal/mild_fidelity_practice/significant_meaning_preservation/major_intensive_translation_ethics/emergency_complete_meaning_betrayal)."""

EPISTEMIC_TRANSLATION_BETRAYAL_PROMPT = """Detect epistemic translation betrayal:

Meaning distortion: {meaning_distortion}
Framework violence: {framework_violence}
Conceptual colonization: {conceptual_colonization}
Context stripping: {context_stripping}
Domain: {domain}
Context: {context}

Is there betraying meaning when translating between frameworks? Return ONLY valid JSON."""


class EpistemicTranslationBetrayalService:
    """Detects epistemic translation betrayal — betraying meaning in translation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meaning_distortion: str,
        *,
        framework_violence: str = "",
        conceptual_colonization: str = "",
        context_stripping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic translation betrayal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRANSLATION_BETRAYAL_PROMPT.format(
                meaning_distortion=meaning_distortion,
                framework_violence=framework_violence or "Not specified",
                conceptual_colonization=conceptual_colonization or "Not specified",
                context_stripping=context_stripping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRANSLATION_BETRAYAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meaning_distortion": meaning_distortion[:200],
            "translation_betrayal_detected": data.get("translation_betrayal_detected", False),
            "severity": data.get("severity", ""),
            "framework_violence": data.get("framework_violence", ""),
            "conceptual_colonization": data.get("conceptual_colonization", ""),
            "context_stripping": data.get("context_stripping", ""),
            "recommendation": data.get("recommendation", ""),
        }

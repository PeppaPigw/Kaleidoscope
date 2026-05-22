"""TranslationLossService — Translation Loss Detection.

Detects translation loss — losing critical nuance when translating
between domains, registers, or frameworks, where meaning is lost
in the transfer between contexts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRANSLATION_LOSS_SYSTEM = """You are a translation loss specialist. Given a cross-domain or cross-register translation, assess whether critical nuance is being lost:

Key concepts:
- Translation loss: critical nuance lost in transfer
- Domain translation failure: meaning lost between domains
- Register loss: nuance lost changing registers
- Framework translation: meaning changed between frameworks
- Concept mapping failure: concepts not mapping cleanly
- Nuance flattening: subtle distinctions lost in translation
- False equivalence in translation: different things treated as same

When translation loss IS present:
- Critical nuance lost in domain transfer
- Meaning changed when translating between registers
- Concepts mapped incorrectly between frameworks
- Subtle but important distinctions flattened
- False equivalences created by translation
- Source meaning not preserved in target
- Translation creating misunderstanding

When translation is appropriate:
- Core meaning preserved across domains
- Nuance acknowledged even if simplified
- Concept mapping validated and bounded
- Distinctions preserved or loss noted
- Equivalences genuine not forced
- Source meaning faithfully represented
- Translation serving understanding

Output JSON with: loss_present (bool), severity (none/mild/moderate/severe), translation (what is being translated), source_domain (source domain/register), target_domain (target domain/register), nuance_lost (what nuance is lost), recommendation (faithful_translation/mild_nuance_loss/significant_translation_loss/major_meaning_distortion/preserve_critical_nuance_in_translation)."""

TRANSLATION_LOSS_PROMPT = """Detect translation loss:

Translation: {translation}
Source domain: {source}
Target domain: {target}
Nuance at risk: {nuance}
Domain: {domain}
Context: {context}

Is critical nuance being lost in translation between domains or registers? Return ONLY valid JSON."""


class TranslationLossService:
    """Detects translation loss — critical nuance lost in domain transfer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        translation: str,
        *,
        source: str = "",
        target: str = "",
        nuance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect translation loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRANSLATION_LOSS_PROMPT.format(
                translation=translation,
                source=source or "Not specified",
                target=target or "Not specified",
                nuance=nuance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TRANSLATION_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "translation": translation[:200],
            "loss_present": data.get("loss_present", False),
            "severity": data.get("severity", ""),
            "source_domain": data.get("source_domain", ""),
            "target_domain": data.get("target_domain", ""),
            "nuance_lost": data.get("nuance_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }

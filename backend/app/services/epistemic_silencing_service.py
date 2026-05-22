"""EpistemicSilencingService — Epistemic Silencing Detection.

Detects epistemic silencing — silencing certain voices or perspectives
from contributing to knowledge, where power dynamics prevent
certain knowers from being heard.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SILENCING_SYSTEM = """You are an epistemic silencing specialist. Given a knowledge production context, assess whether certain voices are being silenced:

Key concepts:
- Epistemic silencing: voices prevented from contributing
- Structural silencing: systems preventing certain voices
- Active silencing: deliberate suppression of perspectives
- Passive silencing: environments that discourage contribution
- Platform denial: access to knowledge platforms denied
- Voice suppression: certain perspectives systematically excluded
- Contribution barriers: obstacles to epistemic participation

When epistemic silencing IS present:
- Certain voices systematically excluded from knowledge production
- Power dynamics preventing contribution
- Structural barriers to epistemic participation
- Active suppression of certain perspectives
- Environments discouraging certain contributions
- Platform access denied to certain knowers
- Systematic exclusion from knowledge-making

When appropriate curation is present:
- Inclusion based on relevance and quality
- Exclusion based on merit not identity
- Barriers serving quality not exclusion
- All relevant perspectives accessible
- Curation transparent and justified
- Participation open to qualified contributors
- Standards applied consistently

Output JSON with: silencing_present (bool), severity (none/mild/moderate/severe), context (what knowledge context), silenced (who/what is silenced), mechanism (how silencing occurs), impact (what knowledge is lost), recommendation (appropriate_curation/mild_exclusion_pattern/significant_epistemic_silencing/major_voice_suppression/ensure_epistemic_inclusion)."""

EPISTEMIC_SILENCING_PROMPT = """Detect epistemic silencing:

Knowledge context: {knowledge_context}
Voices included: {included}
Voices excluded: {excluded}
Barriers: {barriers}
Domain: {domain}
Context: {context}

Are certain voices or perspectives being silenced from contributing to knowledge? Return ONLY valid JSON."""


class EpistemicSilencingService:
    """Detects epistemic silencing — voices prevented from contributing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge_context: str,
        *,
        included: str = "",
        excluded: str = "",
        barriers: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic silencing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SILENCING_PROMPT.format(
                knowledge_context=knowledge_context,
                included=included or "Not specified",
                excluded=excluded or "Not specified",
                barriers=barriers or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SILENCING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge_context": knowledge_context[:200],
            "silencing_present": data.get("silencing_present", False),
            "severity": data.get("severity", ""),
            "silenced": data.get("silenced", ""),
            "mechanism": data.get("mechanism", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicDisdainService — Epistemic Disdain Detection.

Detects epistemic disdain — disdain for ideas deemed beneath
serious intellectual consideration.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISDAIN_SYSTEM = """You are an epistemic disdain specialist. Given disdain for ideas deemed beneath consideration, assess epistemic disdain:

Key concepts:
- Epistemic disdain: disdain for ideas deemed beneath consideration
- Beneath notice: treating ideas as unworthy of engagement
- Intellectual snobbery: only engaging with approved sources
- Quality gatekeeping: rigid standards excluding valid ideas
- Source dismissal: rejecting ideas based on origin not merit
- Aesthetic rejection: dismissing ideas for lacking elegance
- Purity standards: only accepting ideas meeting arbitrary criteria

When epistemic disdain IS present:
- Disdain for ideas deemed beneath
- Treating as unworthy of engagement
- Only engaging approved sources
- Rigid excluding standards
- Rejecting based on origin
- Dismissing for lacking elegance
- Arbitrary purity criteria

When no disdain:
- Open to all ideas
- Engaging with everything
- Diverse sources
- Flexible standards
- Judging on merit
- Accepting diverse forms
- Inclusive criteria

Output JSON with: disdain_detected (bool), severity (none/mild/moderate/severe), beneath_notice (what treating as unworthy), intellectual_snobbery (what only engaging), source_dismissal (what rejecting based on origin), aesthetic_rejection (what dismissing for form), recommendation (no_disdain/mild_openness_practice/significant_inclusion_work/major_intensive_humility_therapy/emergency_active_exclusion)."""

EPISTEMIC_DISDAIN_PROMPT = """Detect epistemic disdain:

Beneath notice: {beneath_notice}
Intellectual snobbery: {intellectual_snobbery}
Source dismissal: {source_dismissal}
Aesthetic rejection: {aesthetic_rejection}
Domain: {domain}
Context: {context}

Is there disdain for ideas deemed beneath serious consideration? Return ONLY valid JSON."""


class EpistemicDisdainService:
    """Detects epistemic disdain — disdain for ideas deemed beneath consideration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        beneath_notice: str,
        *,
        intellectual_snobbery: str = "",
        source_dismissal: str = "",
        aesthetic_rejection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic disdain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISDAIN_PROMPT.format(
                beneath_notice=beneath_notice,
                intellectual_snobbery=intellectual_snobbery or "Not specified",
                source_dismissal=source_dismissal or "Not specified",
                aesthetic_rejection=aesthetic_rejection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISDAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "beneath_notice": beneath_notice[:200],
            "disdain_detected": data.get("disdain_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_snobbery": data.get("intellectual_snobbery", ""),
            "source_dismissal": data.get("source_dismissal", ""),
            "aesthetic_rejection": data.get("aesthetic_rejection", ""),
            "recommendation": data.get("recommendation", ""),
        }

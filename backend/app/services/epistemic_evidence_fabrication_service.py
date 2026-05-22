"""EpistemicEvidenceFabricationService — Epistemic Evidence Fabrication Detection.

Detects epistemic evidence fabrication — fabricating or manufacturing
evidence to support predetermined conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVIDENCE_FABRICATION_SYSTEM = """You are an epistemic evidence fabrication specialist. Given manufactured or fabricated evidence, assess evidence fabrication:

Key concepts:
- Epistemic evidence fabrication: manufacturing evidence to support conclusions
- Data fabrication: creating data that doesn't reflect reality
- Source invention: inventing sources that don't exist
- Quote manipulation: manipulating quotes to change meaning
- Context stripping: stripping context to change evidence meaning
- Selective compilation: compiling evidence selectively to create false picture
- Testimonial fabrication: fabricating testimonials or expert opinions

When epistemic evidence fabrication IS present:
- Evidence manufactured
- Data fabricated
- Sources invented
- Quotes manipulated
- Context stripped
- Compilation selective
- Testimonials fabricated

When no evidence fabrication:
- Evidence genuine
- Data reflects reality
- Sources verifiable
- Quotes accurate
- Context preserved
- Compilation fair
- Testimonials authentic

Output JSON with: evidence_fabrication_detected (bool), severity (none/mild/moderate/severe), data_fabrication (what data fabricated), source_invention (what sources invented), quote_manipulation (what quotes manipulated), context_stripping (what context stripped), recommendation (no_evidence_fabrication/mild_verification_practice/significant_source_checking/major_intensive_evidence_audit/emergency_complete_evidence_fabrication)."""

EPISTEMIC_EVIDENCE_FABRICATION_PROMPT = """Detect epistemic evidence fabrication:

Data fabrication: {data_fabrication}
Source invention: {source_invention}
Quote manipulation: {quote_manipulation}
Context stripping: {context_stripping}
Domain: {domain}
Context: {context}

Is evidence being fabricated or manufactured to support conclusions? Return ONLY valid JSON."""


class EpistemicEvidenceFabricationService:
    """Detects epistemic evidence fabrication — manufactured evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        data_fabrication: str,
        *,
        source_invention: str = "",
        quote_manipulation: str = "",
        context_stripping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evidence fabrication."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVIDENCE_FABRICATION_PROMPT.format(
                data_fabrication=data_fabrication,
                source_invention=source_invention or "Not specified",
                quote_manipulation=quote_manipulation or "Not specified",
                context_stripping=context_stripping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVIDENCE_FABRICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "data_fabrication": data_fabrication[:200],
            "evidence_fabrication_detected": data.get("evidence_fabrication_detected", False),
            "severity": data.get("severity", ""),
            "source_invention": data.get("source_invention", ""),
            "quote_manipulation": data.get("quote_manipulation", ""),
            "context_stripping": data.get("context_stripping", ""),
            "recommendation": data.get("recommendation", ""),
        }

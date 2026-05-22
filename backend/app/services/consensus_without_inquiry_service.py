"""ConsensusWithoutInquiryService — Consensus Without Inquiry Detection.

Detects consensus-without-inquiry — claiming consensus exists without
actual investigation, where agreement is assumed or manufactured
rather than genuinely established through proper inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONSENSUS_WITHOUT_INQUIRY_SYSTEM = """You are a consensus-without-inquiry specialist. Given a consensus claim, assess whether it was established through genuine inquiry:

Key concepts:
- Consensus without inquiry: agreement claimed without investigation
- Manufactured consensus: appearance of agreement without substance
- Assumed agreement: consensus presumed rather than verified
- Survey-free consensus: no actual polling or investigation
- Echo chamber consensus: agreement within a bubble
- Selective consensus: only counting agreeing voices
- Consensus by exclusion: disagreers excluded from count

When consensus-without-inquiry IS present:
- Consensus claimed without systematic investigation
- Agreement assumed rather than verified
- No actual survey or inquiry conducted
- Only agreeing voices counted
- Disagreement excluded from consensus count
- Echo chamber mistaken for broad agreement
- Consensus manufactured through selective citation

When consensus claims are appropriate:
- Systematic investigation conducted
- Methodology for establishing consensus clear
- Disagreement acknowledged and quantified
- Representative sampling of relevant experts
- Consensus boundaries clearly stated
- Process of inquiry transparent
- Limitations of consensus acknowledged

Output JSON with: without_inquiry_present (bool), severity (none/mild/moderate/severe), consensus_claimed (what consensus is claimed), investigation (what investigation was done), excluded (what voices were excluded), methodology (how consensus was established), recommendation (well_established_consensus/mild_inquiry_gap/significant_consensus_without_inquiry/major_manufactured_consensus/conduct_proper_inquiry)."""

CONSENSUS_WITHOUT_INQUIRY_PROMPT = """Detect consensus without inquiry:

Consensus claim: {claim}
Investigation done: {investigation}
Voices included: {included}
Voices excluded: {excluded}
Domain: {domain}
Context: {context}

Is consensus being claimed without genuine investigation? Return ONLY valid JSON."""


class ConsensusWithoutInquiryService:
    """Detects consensus-without-inquiry — agreement claimed without investigation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        investigation: str = "",
        included: str = "",
        excluded: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect consensus without inquiry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONSENSUS_WITHOUT_INQUIRY_PROMPT.format(
                claim=claim,
                investigation=investigation or "Not specified",
                included=included or "Not specified",
                excluded=excluded or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONSENSUS_WITHOUT_INQUIRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "without_inquiry_present": data.get("without_inquiry_present", False),
            "severity": data.get("severity", ""),
            "consensus_claimed": data.get("consensus_claimed", ""),
            "investigation": data.get("investigation", ""),
            "excluded": data.get("excluded", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicEvidenceMisattributionService — Epistemic Evidence Misattribution Detection.

Detects epistemic evidence misattribution — attributing evidence to wrong
sources or causes, creating false provenance chains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVIDENCE_MISATTRIBUTION_SYSTEM = """You are an epistemic evidence misattribution specialist. Given evidence attributed to wrong sources, assess evidence misattribution:

Key concepts:
- Epistemic evidence misattribution: attributing evidence to wrong sources
- Source confusion: confusing the actual source of evidence
- Authority transfer: transferring authority from one source to another
- Provenance loss: losing track of evidence provenance
- Citation laundering: laundering claims through citation chains
- Misquotation: attributing statements to wrong people
- Context transplant: transplanting evidence from one context to another

When epistemic evidence misattribution IS present:
- Evidence attributed wrongly
- Sources confused
- Authority transferred inappropriately
- Provenance lost
- Citations laundered
- Statements misquoted
- Context transplanted

When no evidence misattribution:
- Attribution accurate
- Sources clear
- Authority appropriate
- Provenance tracked
- Citations direct
- Quotes accurate
- Context preserved

Output JSON with: evidence_misattribution_detected (bool), severity (none/mild/moderate/severe), source_confusion (what sources confused), authority_transfer (what authority transferred), provenance_loss (what provenance lost), citation_laundering (what citations laundered), recommendation (no_evidence_misattribution/mild_attribution_checking/significant_provenance_tracking/major_intensive_source_verification/emergency_complete_evidence_misattribution)."""

EPISTEMIC_EVIDENCE_MISATTRIBUTION_PROMPT = """Detect epistemic evidence misattribution:

Source confusion: {source_confusion}
Authority transfer: {authority_transfer}
Provenance loss: {provenance_loss}
Citation laundering: {citation_laundering}
Domain: {domain}
Context: {context}

Is evidence being attributed to wrong sources or causes? Return ONLY valid JSON."""


class EpistemicEvidenceMisattributionService:
    """Detects epistemic evidence misattribution — wrong attribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source_confusion: str,
        *,
        authority_transfer: str = "",
        provenance_loss: str = "",
        citation_laundering: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evidence misattribution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVIDENCE_MISATTRIBUTION_PROMPT.format(
                source_confusion=source_confusion,
                authority_transfer=authority_transfer or "Not specified",
                provenance_loss=provenance_loss or "Not specified",
                citation_laundering=citation_laundering or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVIDENCE_MISATTRIBUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source_confusion": source_confusion[:200],
            "evidence_misattribution_detected": data.get("evidence_misattribution_detected", False),
            "severity": data.get("severity", ""),
            "authority_transfer": data.get("authority_transfer", ""),
            "provenance_loss": data.get("provenance_loss", ""),
            "citation_laundering": data.get("citation_laundering", ""),
            "recommendation": data.get("recommendation", ""),
        }

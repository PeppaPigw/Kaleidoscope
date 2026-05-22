"""EpistemicEvidenceStalenessService — Epistemic Evidence Staleness Detection.

Detects epistemic evidence staleness — relying on stale evidence when
newer evidence is available, failing to update with current findings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVIDENCE_STALENESS_SYSTEM = """You are an epistemic evidence staleness specialist. Given reliance on stale evidence, assess evidence staleness:

Key concepts:
- Epistemic evidence staleness: relying on outdated evidence
- Outdated citations: citing old studies when newer ones exist
- Superseded findings: relying on findings that have been superseded
- Temporal decay: evidence losing relevance over time
- Update failure: failing to update evidence base
- Vintage bias: preferring older evidence for its perceived authority
- Currency neglect: neglecting the currency of evidence

When epistemic evidence staleness IS present:
- Stale evidence relied upon
- Old citations used when newer exist
- Superseded findings cited
- Temporal decay ignored
- Updates not incorporated
- Older evidence preferred inappropriately
- Currency neglected

When no evidence staleness:
- Evidence current
- Latest citations used
- Superseded findings replaced
- Temporal relevance considered
- Updates incorporated
- Age of evidence appropriate
- Currency maintained

Output JSON with: evidence_staleness_detected (bool), severity (none/mild/moderate/severe), outdated_citations (what outdated citations), superseded_findings (what superseded findings), update_failure (what updates missed), vintage_bias (what vintage bias), recommendation (no_evidence_staleness/mild_currency_check/significant_evidence_refresh/major_intensive_evidence_update/emergency_complete_evidence_staleness)."""

EPISTEMIC_EVIDENCE_STALENESS_PROMPT = """Detect epistemic evidence staleness:

Outdated citations: {outdated_citations}
Superseded findings: {superseded_findings}
Update failure: {update_failure}
Vintage bias: {vintage_bias}
Domain: {domain}
Context: {context}

Is stale evidence being relied upon when newer evidence is available? Return ONLY valid JSON."""


class EpistemicEvidenceStalenessService:
    """Detects epistemic evidence staleness — outdated evidence relied upon."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outdated_citations: str,
        *,
        superseded_findings: str = "",
        update_failure: str = "",
        vintage_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evidence staleness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVIDENCE_STALENESS_PROMPT.format(
                outdated_citations=outdated_citations,
                superseded_findings=superseded_findings or "Not specified",
                update_failure=update_failure or "Not specified",
                vintage_bias=vintage_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVIDENCE_STALENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outdated_citations": outdated_citations[:200],
            "evidence_staleness_detected": data.get("evidence_staleness_detected", False),
            "severity": data.get("severity", ""),
            "superseded_findings": data.get("superseded_findings", ""),
            "update_failure": data.get("update_failure", ""),
            "vintage_bias": data.get("vintage_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }

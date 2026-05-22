"""MotivatedScholarshipService — Motivated Scholarship Detection.

Detects motivated scholarship — research or analysis where conclusions
are predetermined by the researcher's commitments, and evidence is
selected or interpreted to support those conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_SCHOLARSHIP_SYSTEM = """You are a motivated scholarship specialist. Given research or analysis, assess whether conclusions are predetermined by the researcher's commitments:

Key concepts:
- Motivated scholarship: conclusions predetermined by commitments
- Advocacy research: research designed to support a position
- Confirmation research: seeking only confirming evidence
- Ideological scholarship: ideology determining conclusions
- Policy-based evidence: evidence selected to support policy
- Conclusion-first research: working backward from desired conclusion
- Selective methodology: methods chosen to produce desired results

When motivated scholarship IS present:
- Conclusions appear predetermined before evidence gathered
- Evidence selected to support pre-existing position
- Disconfirming evidence ignored or explained away
- Methodology chosen to produce desired results
- Research framing reveals advocacy intent
- Alternative interpretations not considered
- Funding source or institutional pressure visible in conclusions

When committed research is appropriate:
- Researcher's position stated transparently
- Evidence genuinely drives conclusions
- Disconfirming evidence addressed honestly
- Methodology appropriate regardless of results
- Alternative interpretations considered
- Commitment motivates inquiry, not conclusions
- Peer review and replication possible

Output JSON with: motivated_present (bool), severity (none/mild/moderate/severe), research (what is researched), predetermined_conclusion (what conclusion seems predetermined), evidence_selection (how evidence is selected), commitment (what commitment drives the research), recommendation (appropriate_committed_research/mild_confirmation_tendency/significant_motivated_scholarship/major_advocacy_research/separate_commitment_from_conclusion)."""

MOTIVATED_SCHOLARSHIP_PROMPT = """Detect motivated scholarship:

Research: {research}
Conclusion: {conclusion}
Evidence handling: {evidence}
Researcher commitment: {commitment}
Domain: {domain}
Context: {context}

Are conclusions predetermined by the researcher's commitments rather than driven by evidence? Return ONLY valid JSON."""


class MotivatedScholarshipService:
    """Detects motivated scholarship — conclusions predetermined by commitments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        research: str,
        *,
        conclusion: str = "",
        evidence: str = "",
        commitment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated scholarship."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_SCHOLARSHIP_PROMPT.format(
                research=research,
                conclusion=conclusion or "Not specified",
                evidence=evidence or "Not specified",
                commitment=commitment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_SCHOLARSHIP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "research": research[:200],
            "motivated_present": data.get("motivated_present", False),
            "severity": data.get("severity", ""),
            "predetermined_conclusion": data.get("predetermined_conclusion", ""),
            "evidence_selection": data.get("evidence_selection", ""),
            "commitment": data.get("commitment", ""),
            "recommendation": data.get("recommendation", ""),
        }

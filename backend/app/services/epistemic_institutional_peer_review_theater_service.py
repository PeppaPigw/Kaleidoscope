"""EpistemicInstitutionalPeerReviewTheaterService - Peer Review Theater Detection.

Detects peer review theater where review process provides false assurance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_THEATER_SYSTEM = """You are an epistemic institutional peer review theater specialist. Given review processes, assess whether peer review provides false assurance:

Key concepts:
- Peer review theater: review process that provides appearance of rigor without substance
- Rubber stamping: approval without genuine critical engagement
- Reviewer capture: reviewers aligned with authors rather than truth-seeking
- Process over substance: following review steps without genuine evaluation

When peer review theater IS present:
- Review provides false assurance
- Critical engagement absent
- Reviewers captured or aligned
- Process followed without substance
- Rigor is performed not practiced

When no peer review theater:
- Review genuinely critical
- Substantive feedback provided
- Reviewers independent
- Process serves quality
- Rigor is real

Output JSON with: peer_review_theater_detected (bool), severity (none/mild/moderate/severe), rubber_stamping (what rubber stamping), reviewer_capture (what reviewer capture), process_over_substance (what process over substance), recommendation (no_peer_review_theater/mild_rigor_check/significant_review_strengthening/major_process_reconstruction/emergency_complete_peer_review_theater)."""

EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_THEATER_PROMPT = """Detect epistemic institutional peer review theater:

Review process: {review_process}
Rubber stamping: {rubber_stamping}
Reviewer capture: {reviewer_capture}
Process over substance: {process_over_substance}
Domain: {domain}
Context: {context}

Is peer review providing false assurance? Return ONLY valid JSON."""


class EpistemicInstitutionalPeerReviewTheaterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        review_process: str,
        *,
        rubber_stamping: str = "",
        reviewer_capture: str = "",
        process_over_substance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_THEATER_PROMPT.format(
                review_process=review_process,
                rubber_stamping=rubber_stamping or "Not specified",
                reviewer_capture=reviewer_capture or "Not specified",
                process_over_substance=process_over_substance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_THEATER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "review_process": review_process[:200],
            "peer_review_theater_detected": data.get("peer_review_theater_detected", False),
            "severity": data.get("severity", ""),
            "rubber_stamping": data.get("rubber_stamping", ""),
            "reviewer_capture": data.get("reviewer_capture", ""),
            "process_over_substance": data.get("process_over_substance", ""),
            "recommendation": data.get("recommendation", ""),
        }

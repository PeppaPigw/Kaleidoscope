"""EpistemicInstitutionalPeerReviewFailureService — Epistemic Peer Review Failure Detection.

Detects epistemic institutional peer review failure — peer review failing to
catch errors, biases, or methodological problems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_FAILURE_SYSTEM = """You are an epistemic institutional peer review failure specialist. Given peer review failure, assess quality control breakdown:

Key concepts:
- Epistemic peer review failure: peer review failing to catch problems
- Reviewer fatigue: overloaded reviewers missing issues
- Expertise mismatch: reviewers lacking relevant expertise
- Confirmation bias in review: reviewers favoring confirming papers
- Old boys network: review favoring established researchers
- Methodological blindness: reviewers missing methodological flaws
- Statistical illiteracy: reviewers unable to evaluate statistics

When epistemic peer review failure IS present:
- Peer review failing to catch errors
- Reviewer fatigue present
- Expertise mismatched
- Confirmation bias in review
- Network effects biasing
- Methodological flaws missed
- Statistical errors uncaught

When no peer review failure:
- Peer review catching problems
- Reviewers fresh and engaged
- Expertise matched
- Review unbiased
- Network effects absent
- Methodology scrutinized
- Statistics verified

Output JSON with: peer_review_failure_detected (bool), severity (none/mild/moderate/severe), reviewer_fatigue (what reviewer fatigue), expertise_mismatch (what expertise mismatch), confirmation_bias_review (what confirmation bias), methodological_blindness (what methodology missed), recommendation (no_peer_review_failure/mild_review_improvement/significant_review_reform/major_intensive_review_overhaul/emergency_complete_peer_review_failure)."""

EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_FAILURE_PROMPT = """Detect epistemic institutional peer review failure:

Reviewer fatigue: {reviewer_fatigue}
Expertise mismatch: {expertise_mismatch}
Confirmation bias review: {confirmation_bias_review}
Methodological blindness: {methodological_blindness}
Domain: {domain}
Context: {context}

Is peer review failing to catch errors and biases? Return ONLY valid JSON."""


class EpistemicInstitutionalPeerReviewFailureService:
    """Detects epistemic peer review failure — quality control breakdown."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reviewer_fatigue: str,
        *,
        expertise_mismatch: str = "",
        confirmation_bias_review: str = "",
        methodological_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional peer review failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_FAILURE_PROMPT.format(
                reviewer_fatigue=reviewer_fatigue,
                expertise_mismatch=expertise_mismatch or "Not specified",
                confirmation_bias_review=confirmation_bias_review or "Not specified",
                methodological_blindness=methodological_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_PEER_REVIEW_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reviewer_fatigue": reviewer_fatigue[:200],
            "peer_review_failure_detected": data.get("peer_review_failure_detected", False),
            "severity": data.get("severity", ""),
            "expertise_mismatch": data.get("expertise_mismatch", ""),
            "confirmation_bias_review": data.get("confirmation_bias_review", ""),
            "methodological_blindness": data.get("methodological_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }

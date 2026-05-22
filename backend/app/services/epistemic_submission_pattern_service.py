"""EpistemicSubmissionPatternService — Epistemic Submission Pattern Detection.

Detects epistemic submission pattern — submitting intellectually to
authority without critical evaluation of their claims.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUBMISSION_PATTERN_SYSTEM = """You are an epistemic submission pattern specialist. Given submitting to authority without evaluation, assess submission pattern:

Key concepts:
- Epistemic submission pattern: submitting to authority without critical evaluation
- Uncritical deference: deferring without evaluating
- Authority worship: worshipping authority figures intellectually
- Intellectual surrender: surrendering own judgment to authority
- Critical faculty suspension: suspending critical thinking for authority
- Obedience over truth: valuing obedience to authority over truth
- Autonomy abdication: abdicating intellectual autonomy

When epistemic submission pattern IS present:
- Submitting without evaluation
- Deferring uncritically
- Worshipping authority
- Surrendering own judgment
- Suspending critical thinking
- Valuing obedience over truth
- Abdicating autonomy

When no submission pattern:
- Evaluating before accepting
- Critical deference
- Respecting without worshipping
- Maintaining own judgment
- Critical thinking active
- Valuing truth over obedience
- Maintaining autonomy

Output JSON with: submission_pattern_detected (bool), severity (none/mild/moderate/severe), uncritical_deference (who deferring to uncritically), authority_worship (whose authority worshipped), intellectual_surrender (what judgment surrendered about), autonomy_abdication (what autonomy abdicated about), recommendation (no_submission_pattern/mild_critical_practice/significant_autonomy_building/major_intensive_independence/emergency_complete_intellectual_submission)."""

EPISTEMIC_SUBMISSION_PATTERN_PROMPT = """Detect epistemic submission pattern:

Uncritical deference: {uncritical_deference}
Authority worship: {authority_worship}
Intellectual surrender: {intellectual_surrender}
Autonomy abdication: {autonomy_abdication}
Domain: {domain}
Context: {context}

Is there submitting intellectually to authority without critical evaluation? Return ONLY valid JSON."""


class EpistemicSubmissionPatternService:
    """Detects epistemic submission pattern — submitting without evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        uncritical_deference: str,
        *,
        authority_worship: str = "",
        intellectual_surrender: str = "",
        autonomy_abdication: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic submission pattern."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUBMISSION_PATTERN_PROMPT.format(
                uncritical_deference=uncritical_deference,
                authority_worship=authority_worship or "Not specified",
                intellectual_surrender=intellectual_surrender or "Not specified",
                autonomy_abdication=autonomy_abdication or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUBMISSION_PATTERN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "uncritical_deference": uncritical_deference[:200],
            "submission_pattern_detected": data.get("submission_pattern_detected", False),
            "severity": data.get("severity", ""),
            "authority_worship": data.get("authority_worship", ""),
            "intellectual_surrender": data.get("intellectual_surrender", ""),
            "autonomy_abdication": data.get("autonomy_abdication", ""),
            "recommendation": data.get("recommendation", ""),
        }

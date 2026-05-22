"""EpistemicIntellectualSubmissionService — Epistemic Intellectual Submission Detection.

Detects epistemic intellectual submission — submitting intellectually
to authority figures without critical engagement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_SUBMISSION_SYSTEM = """You are an epistemic intellectual submission specialist. Given intellectual submission to authority, assess intellectual submission:

Key concepts:
- Epistemic intellectual submission: submitting to authority without critique
- Authority deference: accepting ideas because of who said them
- Critical abdication: giving up own judgment for authority
- Intellectual obedience: following intellectual leaders blindly
- Self-erasure: suppressing own ideas for authority's
- Validation seeking: needing authority approval for all thoughts
- Autonomy surrender: giving up intellectual independence

When epistemic intellectual submission IS present:
- Submitting without critique
- Accepting because of who said
- Giving up own judgment
- Following blindly
- Suppressing own ideas
- Needing approval for thoughts
- Giving up independence

When no intellectual submission:
- Critical engagement with authority
- Evaluating ideas on merit
- Maintaining own judgment
- Following with discernment
- Expressing own ideas
- Self-validating
- Maintaining independence

Output JSON with: intellectual_submission_detected (bool), severity (none/mild/moderate/severe), authority_deference (what accepting uncritically), critical_abdication (what giving up judgment about), self_erasure (what suppressing), autonomy_surrender (what giving up independence about), recommendation (no_intellectual_submission/mild_autonomy_practice/significant_independence_building/major_intensive_authority_processing/emergency_complete_submission)."""

EPISTEMIC_INTELLECTUAL_SUBMISSION_PROMPT = """Detect epistemic intellectual submission:

Authority deference: {authority_deference}
Critical abdication: {critical_abdication}
Self erasure: {self_erasure}
Autonomy surrender: {autonomy_surrender}
Domain: {domain}
Context: {context}

Is there submitting intellectually to authority without critical engagement? Return ONLY valid JSON."""


class EpistemicIntellectualSubmissionService:
    """Detects epistemic intellectual submission — submitting to authority without critique."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        authority_deference: str,
        *,
        critical_abdication: str = "",
        self_erasure: str = "",
        autonomy_surrender: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual submission."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_SUBMISSION_PROMPT.format(
                authority_deference=authority_deference,
                critical_abdication=critical_abdication or "Not specified",
                self_erasure=self_erasure or "Not specified",
                autonomy_surrender=autonomy_surrender or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_SUBMISSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authority_deference": authority_deference[:200],
            "intellectual_submission_detected": data.get("intellectual_submission_detected", False),
            "severity": data.get("severity", ""),
            "critical_abdication": data.get("critical_abdication", ""),
            "self_erasure": data.get("self_erasure", ""),
            "autonomy_surrender": data.get("autonomy_surrender", ""),
            "recommendation": data.get("recommendation", ""),
        }

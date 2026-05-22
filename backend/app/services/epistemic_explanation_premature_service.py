"""EpistemicExplanationPrematureService — Epistemic Premature Explanation Detection.

Detects epistemic premature explanation — explaining before sufficient
evidence is gathered, jumping to explanations prematurely.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLANATION_PREMATURE_SYSTEM = """You are an epistemic premature explanation specialist. Given premature explanations, assess explanation prematurity:

Key concepts:
- Epistemic premature explanation: explaining before sufficient evidence
- Explanation urgency: feeling urgent need to explain before ready
- Pattern completion: completing pattern before data warrants
- Closure need: needing closure driving premature explanation
- First explanation fixation: fixating on first explanation that comes to mind
- Ambiguity intolerance: intolerance of ambiguity driving premature explanation
- Explanation lock-in: locking into explanation before alternatives explored

When epistemic premature explanation IS present:
- Explanation offered before evidence sufficient
- Urgency to explain
- Patterns completed prematurely
- Closure need driving
- First explanation fixated on
- Ambiguity not tolerated
- Explanation locked in early

When no premature explanation:
- Explanation waits for evidence
- Patience with uncertainty
- Patterns verified before completing
- Closure not rushed
- Multiple explanations considered
- Ambiguity tolerated
- Explanation remains tentative

Output JSON with: premature_explanation_detected (bool), severity (none/mild/moderate/severe), explanation_urgency (what urgency driving), pattern_completion (what patterns completed prematurely), closure_need (what closure need), first_explanation_fixation (what first explanation fixated), recommendation (no_premature_explanation/mild_patience_practice/significant_evidence_waiting/major_intensive_explanation_deferral/emergency_complete_premature_explanation)."""

EPISTEMIC_EXPLANATION_PREMATURE_PROMPT = """Detect epistemic premature explanation:

Explanation urgency: {explanation_urgency}
Pattern completion: {pattern_completion}
Closure need: {closure_need}
First explanation fixation: {first_explanation_fixation}
Domain: {domain}
Context: {context}

Are explanations being offered before sufficient evidence is gathered? Return ONLY valid JSON."""


class EpistemicExplanationPrematureService:
    """Detects epistemic premature explanation — explaining too early."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation_urgency: str,
        *,
        pattern_completion: str = "",
        closure_need: str = "",
        first_explanation_fixation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic premature explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLANATION_PREMATURE_PROMPT.format(
                explanation_urgency=explanation_urgency,
                pattern_completion=pattern_completion or "Not specified",
                closure_need=closure_need or "Not specified",
                first_explanation_fixation=first_explanation_fixation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLANATION_PREMATURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation_urgency": explanation_urgency[:200],
            "premature_explanation_detected": data.get("premature_explanation_detected", False),
            "severity": data.get("severity", ""),
            "pattern_completion": data.get("pattern_completion", ""),
            "closure_need": data.get("closure_need", ""),
            "first_explanation_fixation": data.get("first_explanation_fixation", ""),
            "recommendation": data.get("recommendation", ""),
        }

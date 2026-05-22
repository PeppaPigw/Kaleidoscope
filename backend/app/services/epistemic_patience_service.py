"""EpistemicPatienceService — Epistemic Patience Failure Detection.

Detects epistemic patience failure — inability to tolerate the
uncertainty and ambiguity required for genuine understanding,
rushing to premature conclusions to relieve discomfort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PATIENCE_SYSTEM = """You are an epistemic patience failure specialist. Given a reasoning process, assess whether impatience is producing premature conclusions:

Key concepts:
- Epistemic patience failure: rushing to premature conclusions
- Ambiguity intolerance: discomfort with uncertainty driving closure
- Premature cognitive closure: closing inquiry too early
- Negative capability failure: inability to remain in uncertainty
- Comfort-seeking epistemology: conclusions for comfort not truth
- Deliberation truncation: cutting reasoning short
- Satisficing as impatience: accepting first adequate answer

When epistemic patience failure IS present:
- Conclusions reached before adequate evidence
- Ambiguity discomfort driving premature closure
- Inquiry closed before questions resolved
- Uncertainty relieved through assertion not evidence
- First adequate answer accepted without exploration
- Reasoning truncated for comfort
- Complexity avoided through premature simplification

When decisive action is appropriate:
- Evidence genuinely sufficient for conclusion
- Closure based on adequate investigation
- Remaining uncertainty acknowledged
- Decision made with appropriate confidence
- Further inquiry unlikely to change conclusion
- Time constraints genuine and acknowledged
- Conclusion proportional to evidence

Output JSON with: impatience_present (bool), severity (none/mild/moderate/severe), process (what reasoning process), premature (what is premature), discomfort (what discomfort drives closure), missed (what is missed by rushing), recommendation (appropriate_decisive_action/mild_premature_closure/significant_epistemic_impatience/major_deliberation_failure/practice_epistemic_patience)."""

EPISTEMIC_PATIENCE_PROMPT = """Detect epistemic patience failure:

Reasoning process: {process}
Conclusion reached: {conclusion}
Evidence available: {evidence}
Uncertainty remaining: {uncertainty}
Domain: {domain}
Context: {context}

Is impatience producing premature conclusions before adequate evidence? Return ONLY valid JSON."""


class EpistemicPatienceService:
    """Detects epistemic patience failure — rushing to premature conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process: str,
        *,
        conclusion: str = "",
        evidence: str = "",
        uncertainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic patience failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PATIENCE_PROMPT.format(
                process=process,
                conclusion=conclusion or "Not specified",
                evidence=evidence or "Not specified",
                uncertainty=uncertainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PATIENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process": process[:200],
            "impatience_present": data.get("impatience_present", False),
            "severity": data.get("severity", ""),
            "premature": data.get("premature", ""),
            "discomfort": data.get("discomfort", ""),
            "missed": data.get("missed", ""),
            "recommendation": data.get("recommendation", ""),
        }

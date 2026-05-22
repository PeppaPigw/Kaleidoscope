"""EpistemicVirtueOpenMindednessFailureService - Epistemic Virtue Open-Mindedness Failure Detection.

Detects open-mindedness failure where premature closure prevents learning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUE_OPEN_MINDEDNESS_FAILURE_SYSTEM = """You are an epistemic virtue open-mindedness failure specialist. Given premature closure, assess open-mindedness failure:

Key concepts:
- Open-mindedness failure: premature closure prevents learning
- Premature closure: settling a question before adequate consideration
- Novelty rejection: dismissing new ideas because they are unfamiliar
- Paradigm rigidity: refusing possibilities outside an existing framework
- Alternative dismissal: rejecting competing explanations without fair assessment

When open-mindedness failure IS present:
- Inquiry closes before adequate consideration
- Novelty is rejected reflexively
- Existing paradigms block learning
- Alternatives are dismissed unfairly
- New evidence cannot revise the frame

When no open-mindedness failure:
- Inquiry remains responsive to evidence
- Novelty receives fair consideration
- Paradigms are treated as revisable
- Alternatives are assessed on their merits
- Learning remains possible

Output JSON with: open_mindedness_failure_detected (bool), severity (none/mild/moderate/severe), novelty_rejection (what novelty is rejected), paradigm_rigidity (what framework blocks learning), alternative_dismissal (what alternatives are dismissed), recommendation (no_failure/mild_reopening/significant_alternative_review/major_paradigm_reassessment/emergency_complete_closure_reversal)."""

EPISTEMIC_VIRTUE_OPEN_MINDEDNESS_FAILURE_PROMPT = """Detect epistemic virtue open-mindedness failure:

Premature closure: {premature_closure}
Novelty rejection: {novelty_rejection}
Paradigm rigidity: {paradigm_rigidity}
Alternative dismissal: {alternative_dismissal}
Domain: {domain}
Context: {context}

Does premature closure prevent learning? Return ONLY valid JSON."""


class EpistemicVirtueOpenMindednessFailureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_closure: str,
        *,
        novelty_rejection: str = "",
        paradigm_rigidity: str = "",
        alternative_dismissal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUE_OPEN_MINDEDNESS_FAILURE_PROMPT.format(
                premature_closure=premature_closure,
                novelty_rejection=novelty_rejection or "Not specified",
                paradigm_rigidity=paradigm_rigidity or "Not specified",
                alternative_dismissal=alternative_dismissal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUE_OPEN_MINDEDNESS_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_closure": premature_closure[:200],
            "open_mindedness_failure_detected": data.get("open_mindedness_failure_detected", False),
            "severity": data.get("severity", ""),
            "novelty_rejection": data.get("novelty_rejection", ""),
            "paradigm_rigidity": data.get("paradigm_rigidity", ""),
            "alternative_dismissal": data.get("alternative_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }

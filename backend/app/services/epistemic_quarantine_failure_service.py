"""EpistemicQuarantineFailureService — Epistemic Quarantine Failure Detection.

Detects epistemic quarantine failure — failure to contain harmful
ideas within appropriate boundaries.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUARANTINE_FAILURE_SYSTEM = """You are an epistemic quarantine failure specialist. Given a containment pattern, assess whether harmful ideas escape appropriate boundaries:

Key concepts:
- Quarantine failure: harmful ideas escaping containment
- Boundary breach: ideas crossing appropriate boundaries
- Containment collapse: containment mechanisms failing
- Context escape: ideas escaping appropriate context
- Domain leakage: harmful ideas leaking across domains
- Normalization: harmful ideas becoming normalized outside quarantine
- Mainstreaming: fringe harmful ideas entering mainstream

When quarantine failure IS present:
- Harmful ideas escaping appropriate containment
- Ideas crossing boundaries they should not cross
- Containment mechanisms failing to hold
- Ideas escaping their appropriate context
- Harmful ideas leaking across domain boundaries
- Harmful ideas becoming normalized outside quarantine
- Fringe harmful ideas entering mainstream discourse

When appropriate containment is present:
- Harmful ideas appropriately contained
- Boundaries maintained effectively
- Containment mechanisms functioning
- Ideas remaining in appropriate context
- Domain boundaries respected
- Harmful ideas not normalized
- Fringe ideas remaining fringe

Output JSON with: quarantine_failure_present (bool), severity (none/mild/moderate/severe), idea (what idea escapes), boundary (what boundary fails), mechanism (how containment fails), normalization (degree of normalization), recommendation (appropriate_containment/mild_leakage/significant_quarantine_failure/major_mainstreaming/restore_containment)."""

EPISTEMIC_QUARANTINE_FAILURE_PROMPT = """Detect epistemic quarantine failure:

Idea: {idea}
Boundary: {boundary}
Mechanism: {mechanism}
Normalization: {normalization}
Domain: {domain}
Context: {context}

Are harmful ideas escaping appropriate containment boundaries? Return ONLY valid JSON."""


class EpistemicQuarantineFailureService:
    """Detects epistemic quarantine failure — harmful ideas escaping containment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        boundary: str = "",
        mechanism: str = "",
        normalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quarantine failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUARANTINE_FAILURE_PROMPT.format(
                idea=idea,
                boundary=boundary or "Not specified",
                mechanism=mechanism or "Not specified",
                normalization=normalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUARANTINE_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "quarantine_failure_present": data.get("quarantine_failure_present", False),
            "severity": data.get("severity", ""),
            "boundary": data.get("boundary", ""),
            "mechanism": data.get("mechanism", ""),
            "normalization": data.get("normalization", ""),
            "recommendation": data.get("recommendation", ""),
        }

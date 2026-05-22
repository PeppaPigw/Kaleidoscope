"""AmbiguityIntoleranceService — Ambiguity Intolerance Detection.

Detects ambiguity intolerance — premature resolution of genuine
ambiguity to reduce discomfort, forcing clarity where uncertainty
is the honest state.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AMBIGUITY_INTOLERANCE_SYSTEM = """You are an ambiguity intolerance specialist. Given a conclusion or decision, assess whether genuine ambiguity is being prematurely resolved:

Key concepts:
- Ambiguity intolerance: discomfort with uncertainty driving premature closure
- Premature resolution: forcing clarity before evidence warrants it
- Need for closure: psychological drive to eliminate uncertainty
- False dichotomy: reducing ambiguous situation to binary choice
- Forced categorization: putting ambiguous cases into clear categories
- Uncertainty avoidance: preferring wrong answer to no answer
- Negative capability: ability to remain in uncertainty

When ambiguity intolerance IS present:
- Genuine ambiguity resolved without sufficient evidence
- Binary categories forced on continuous or ambiguous reality
- Uncertainty eliminated through assertion rather than evidence
- Premature conclusions drawn to avoid discomfort
- Ambiguous cases forced into clear categories
- "I don't know" avoided when it's the honest answer
- Complexity reduced to simplicity prematurely

When ambiguity is appropriately handled:
- Uncertainty acknowledged and maintained where warranted
- Ambiguous cases recognized as ambiguous
- Conclusions proportional to evidence
- "I don't know" used when appropriate
- Complexity preserved when reality is complex
- Decisions made under acknowledged uncertainty
- Negative capability practiced

Output JSON with: intolerance_present (bool), severity (none/mild/moderate/severe), situation (what ambiguous situation), resolution (how ambiguity was resolved), evidence_gap (what evidence is missing), honest_state (what the honest uncertainty level is), recommendation (ambiguity_tolerated/mild_premature_closure/significant_forced_clarity/major_ambiguity_intolerance/maintain_uncertainty)."""

AMBIGUITY_INTOLERANCE_PROMPT = """Detect ambiguity intolerance:

Conclusion: {conclusion}
Evidence: {evidence}
Uncertainty: {uncertainty}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is genuine ambiguity being prematurely resolved to reduce discomfort? Return ONLY valid JSON."""


class AmbiguityIntoleranceService:
    """Detects ambiguity intolerance — premature resolution of genuine uncertainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        evidence: str = "",
        uncertainty: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ambiguity intolerance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AMBIGUITY_INTOLERANCE_PROMPT.format(
                conclusion=conclusion,
                evidence=evidence or "Not specified",
                uncertainty=uncertainty or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AMBIGUITY_INTOLERANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "intolerance_present": data.get("intolerance_present", False),
            "severity": data.get("severity", ""),
            "resolution": data.get("resolution", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "honest_state": data.get("honest_state", ""),
            "recommendation": data.get("recommendation", ""),
        }

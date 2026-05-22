"""DeepDisagreementService — Deep Disagreement Detection.

Detects deep disagreement — disagreements that cannot be resolved
by evidence because they stem from different fundamental frameworks,
values, or epistemic standards.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEEP_DISAGREEMENT_SYSTEM = """You are a deep disagreement specialist. Given a disagreement, assess whether it is deep (framework-level) rather than surface (evidence-level):

Key concepts:
- Deep disagreement: disagreement at framework level
- Incommensurable frameworks: no shared standard for resolution
- Value disagreement: different fundamental values, not facts
- Epistemic standard disagreement: different standards of evidence
- Paradigm difference: operating in different paradigms
- Talking past each other: apparent disagreement from different frames
- Shallow vs. deep: evidence-resolvable vs. framework-level

When deep disagreement IS present:
- Disagreement persists despite sharing all evidence
- Different fundamental frameworks generating different conclusions
- No shared standard for adjudicating the dispute
- Value differences underlying factual disagreements
- Parties operating from incommensurable paradigms
- More evidence won't resolve the disagreement
- Disagreement about what counts as evidence

When disagreement is resolvable:
- Shared framework with different evidence
- Disagreement about facts, not values
- Common standards for evaluation
- More evidence would resolve dispute
- Parties agree on what would change their minds
- Disagreement from information asymmetry
- Shared paradigm with different conclusions

Output JSON with: deep_present (bool), severity (none/mild/moderate/severe), disagreement (what is disagreed about), framework_a (first framework), framework_b (second framework), resolution_barrier (what prevents resolution), recommendation (resolvable_disagreement/mild_framework_tension/significant_deep_disagreement/major_incommensurability/acknowledge_framework_difference)."""

DEEP_DISAGREEMENT_PROMPT = """Detect deep disagreement:

Disagreement: {disagreement}
Position A: {position_a}
Position B: {position_b}
Evidence shared: {evidence}
Domain: {domain}
Context: {context}

Is this a deep disagreement stemming from different frameworks rather than different evidence? Return ONLY valid JSON."""


class DeepDisagreementService:
    """Detects deep disagreement — framework-level rather than evidence-level disputes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        position_a: str = "",
        position_b: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deep disagreement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEEP_DISAGREEMENT_PROMPT.format(
                disagreement=disagreement,
                position_a=position_a or "Not specified",
                position_b=position_b or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEEP_DISAGREEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "deep_present": data.get("deep_present", False),
            "severity": data.get("severity", ""),
            "framework_a": data.get("framework_a", ""),
            "framework_b": data.get("framework_b", ""),
            "resolution_barrier": data.get("resolution_barrier", ""),
            "recommendation": data.get("recommendation", ""),
        }

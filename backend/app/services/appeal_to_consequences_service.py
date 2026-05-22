"""AppealToConsequencesService — Appeal to Consequences Detection.

Detects appeal to consequences (argumentum ad consequentiam) —
arguing that something is true or false based on whether its
consequences are desirable or undesirable. The desirability of
a belief's consequences has no bearing on its truth value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_CONSEQUENCES_SYSTEM = """You are an appeal to consequences specialist. Given an argument, assess whether truth is being determined by desirability of consequences:

Key concepts:
- Argumentum ad consequentiam: truth determined by consequences
- Wishful thinking: believing because you want it to be true
- Pragmatic fallacy: useful ≠ true
- Motivational reasoning: desired outcomes driving belief
- Is-ought confusion: what we want to be true vs what is true
- Pascal's wager: related but distinct (decision vs truth)
- Legitimate pragmatism: consequences matter for decisions, not truth

When appeal to consequences IS present:
- "X can't be true because that would be terrible"
- "We must believe Y because the alternative is unacceptable"
- "If X were true, society would collapse, so X must be false"
- Rejecting evidence because the conclusion is unpleasant
- "It would be nice if X, therefore X is true"
- Using fear of consequences to dismiss factual claims
- "We can't accept that because of what it would mean"

When appeal to consequences is NOT present:
- Consequences are discussed as part of a decision (not truth claim)
- The argument is about what to DO, not what is TRUE
- Consequences are used to motivate investigation, not determine truth
- Risk assessment appropriately considers outcomes
- The argument acknowledges truth is independent of desirability
- Pragmatic considerations are applied to action, not belief
- Consequences inform policy without determining facts

Output JSON with: appeal_to_consequences_present (bool), severity (none/mild/moderate/severe), claim (what truth claim is at stake), consequences_cited (what consequences are invoked), direction (positive appeal or negative appeal), truth_independence (is truth being confused with desirability), recommendation (no_appeal_to_consequences/mild_wishful_thinking/significant_appeal_to_consequences/major_truth_consequence_confusion/separate_truth_from_desirability)."""

APPEAL_CONSEQUENCES_PROMPT = """Detect appeal to consequences:

Argument: {argument}
Claim: {claim}
Consequences cited: {consequences}
Direction: {direction}
Domain: {domain}
Context: {context}

Is truth being determined by the desirability of consequences? Return ONLY valid JSON."""


class AppealToConsequencesService:
    """Detects appeal to consequences — truth determined by desirability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        claim: str = "",
        consequences: str = "",
        direction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to consequences."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_CONSEQUENCES_PROMPT.format(
                argument=argument,
                claim=claim or "Not specified",
                consequences=consequences or "Not specified",
                direction=direction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_CONSEQUENCES_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_consequences_present": data.get("appeal_to_consequences_present", False),
            "severity": data.get("severity", ""),
            "claim": data.get("claim", ""),
            "consequences_cited": data.get("consequences_cited", ""),
            "truth_independence": data.get("truth_independence", ""),
            "recommendation": data.get("recommendation", ""),
        }

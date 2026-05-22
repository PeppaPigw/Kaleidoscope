"""NoTrueScotsman — No True Scotsman Detection.

Detects no true Scotsman fallacy — redefining a category ad hoc
to exclude counterexamples, making the claim unfalsifiable by
moving the definition rather than accepting the counterevidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NO_TRUE_SCOTSMAN_SYSTEM = """You are a no true Scotsman specialist. Given an argument, assess whether it redefines a category to exclude counterexamples:

Key concepts:
- No true Scotsman: ad hoc redefinition to exclude counterexamples
- Moving the definition: changing what counts as X when faced with a counterexample
- Unfalsifiability: making a claim immune to disproof by definition
- Ad hoc rescue: saving a generalization by narrowing it after the fact
- Stipulative definition: legitimate narrowing vs fallacious exclusion
- Essential vs accidental properties: what genuinely defines a category
- Counterexample handling: legitimate refinement vs illegitimate exclusion

When no true Scotsman IS present:
- "No real X would do Y" (when faced with X who did Y)
- Redefining the category AFTER a counterexample is presented
- "That's not REAL socialism/capitalism/etc." to dismiss failures
- Adding qualifications that weren't part of the original claim
- Making a universal claim unfalsifiable by excluding all counterexamples
- "Any X who does Y isn't really X" without independent justification
- Circular definition: X is defined by not-doing-Y, then claiming no X does Y

When no true Scotsman is NOT present:
- The category has a clear, pre-existing definition that excludes the case
- The refinement is based on established criteria, not ad hoc
- The distinction between genuine and non-genuine members is principled
- Counterexamples are acknowledged and the claim is modified
- The definition was stated before the counterexample arose
- Legitimate subcategory distinction with independent justification
- The exclusion is based on definitional, not empirical grounds

Output JSON with: no_true_scotsman_present (bool), severity (none/mild/moderate/severe), original_claim (the initial generalization), counterexample (what counterexample was raised), redefinition (how the category was narrowed), ad_hoc (is the redefinition ad hoc or principled), recommendation (no_fallacy/mild_redefinition/significant_no_true_scotsman/major_unfalsifiability/accept_counterexample)."""

NO_TRUE_SCOTSMAN_PROMPT = """Detect no true Scotsman:

Argument: {argument}
Original claim: {original_claim}
Counterexample: {counterexample}
Response: {response_to_counter}
Domain: {domain}
Context: {context}

Does this redefine a category to exclude counterexamples? Return ONLY valid JSON."""


class NoTrueScotsman:
    """Detects no true Scotsman — ad hoc redefinition to exclude counterexamples."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        original_claim: str = "",
        counterexample: str = "",
        response_to_counter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect no true Scotsman."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NO_TRUE_SCOTSMAN_PROMPT.format(
                argument=argument,
                original_claim=original_claim or "Not specified",
                counterexample=counterexample or "Not specified",
                response_to_counter=response_to_counter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NO_TRUE_SCOTSMAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "no_true_scotsman_present": data.get("no_true_scotsman_present", False),
            "severity": data.get("severity", ""),
            "original_claim": data.get("original_claim", ""),
            "counterexample": data.get("counterexample", ""),
            "redefinition": data.get("redefinition", ""),
            "recommendation": data.get("recommendation", ""),
        }

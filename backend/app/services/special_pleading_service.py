"""SpecialPleadingService — Special Pleading Detection.

Detects special pleading — applying rules, standards, or
principles to others while claiming an unjustified exception
for oneself or one's preferred position. Double standards
without principled justification.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SPECIAL_PLEADING_SYSTEM = """You are a special pleading specialist. Given an argument, assess whether it claims an unjustified exception to a general rule:

Key concepts:
- Special pleading: claiming an exception without justification
- Double standard: applying different rules to similar cases
- Ad hoc exception: creating a rule exception only when it suits
- Principled exception: some exceptions ARE justified (distinguish)
- Consistency: applying the same standards to all similar cases
- Self-serving bias: exceptions that conveniently benefit the arguer
- Universal principles: rules that should apply equally

When special pleading IS present:
- "The rule applies to everyone else, but my case is different" (without justification)
- Applying strict standards to opponents but lax standards to allies
- "That's different" without explaining how it's relevantly different
- Claiming immunity from criticism that one applies to others
- Moving between strict and loose interpretations as convenient
- "Rules for thee but not for me"
- Demanding evidence from others while accepting one's own claims uncritically

When special pleading is NOT present:
- The exception is based on a relevant, principled distinction
- Different treatment is justified by genuinely different circumstances
- The exception is acknowledged and its justification is explicit
- The same exception would be granted to anyone in similar circumstances
- Context genuinely makes the cases different in relevant ways
- The distinction is based on established principles, not convenience
- The arguer would accept the same exception for their opponents

Output JSON with: special_pleading_present (bool), severity (none/mild/moderate/severe), rule (what general principle is invoked), exception_claimed (what exception is claimed), justification (what justification is offered), principled (is the exception principled or ad hoc), consistency (would the same exception be granted to others), recommendation (no_special_pleading/mild_inconsistency/significant_special_pleading/major_double_standard/apply_consistently)."""

SPECIAL_PLEADING_PROMPT = """Detect special pleading:

Argument: {argument}
Rule applied: {rule}
Exception claimed: {exception}
Justification: {justification}
Domain: {domain}
Context: {context}

Does this claim an unjustified exception to a general rule? Return ONLY valid JSON."""


class SpecialPleadingService:
    """Detects special pleading — claiming unjustified exceptions to rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        rule: str = "",
        exception: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect special pleading."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SPECIAL_PLEADING_PROMPT.format(
                argument=argument,
                rule=rule or "Not specified",
                exception=exception or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SPECIAL_PLEADING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "special_pleading_present": data.get("special_pleading_present", False),
            "severity": data.get("severity", ""),
            "rule": data.get("rule", ""),
            "exception_claimed": data.get("exception_claimed", ""),
            "principled": data.get("principled", ""),
            "recommendation": data.get("recommendation", ""),
        }

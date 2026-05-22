"""FullyGeneralCounterargumentService — Fully General Counterargument Detection.

Detects fully general counterarguments — arguments that could be
used to dismiss ANY position regardless of its truth value. If an
argument works equally well against true claims and false claims,
it provides zero evidence. "You only believe that because of your
upbringing" applies to every belief, true or false, and therefore
distinguishes nothing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FULLY_GENERAL_COUNTERARGUMENT_SYSTEM = """You are a fully general counterargument specialist. Given an argument or dismissal, assess whether it could be applied to any position regardless of truth value:

Key concepts (Yudkowsky, 2009):
- Fully general counterargument: works against any claim, true or false
- Zero evidential value: doesn't distinguish true from false claims
- Genetic fallacy variant: dismissing based on origin rather than content
- Unfalsifiable dismissal: no possible evidence could overcome it
- Symmetric argument: applies equally to both sides of any debate
- Thought-terminating cliche: stops thinking without providing information
- Kafkatrap variant: any response confirms the accusation

When fully general counterargument IS present:
- "You only believe that because..." (applies to all beliefs)
- "That's just your opinion" (applies to all statements)
- "You can't prove a negative" (used to dismiss all skepticism)
- "Follow the money" (applies to any funded research, pro or con)
- "That's what they want you to think" (unfalsifiable)
- "You're just rationalizing" (applies to any reasoning)
- "Correlation isn't causation" (used to dismiss all correlational evidence)

When the argument IS specific and valid:
- It applies to this specific claim but not its negation
- It identifies a specific flaw in this particular argument
- It would NOT work equally well against the opposite conclusion
- It provides actual evidence or identifies actual logical errors
- It distinguishes between true and false versions of the claim

Output JSON with: fully_general_present (bool), severity (none/mild/moderate/severe), argument (what counterargument is being used), target_claim (what claim is being dismissed), symmetry_test (does it work equally against the opposite claim), evidential_value (does it distinguish true from false), specificity (is it specific to this claim or general), alternative_dismissal (could it dismiss any claim), recommendation (argument_specific/mild_generality/significant_fully_general/major_zero_evidence_dismissal/use_specific_counterarguments)."""

FULLY_GENERAL_COUNTERARGUMENT_PROMPT = """Detect fully general counterargument:

Argument: {argument}
Target: {target}
Symmetry: {symmetry}
Specificity: {specificity}
Domain: {domain}
Context: {context}

Could this counterargument be used to dismiss any position regardless of truth value? Return ONLY valid JSON."""


class FullyGeneralCounterargumentService:
    """Detects fully general counterarguments — arguments that dismiss anything."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        target: str = "",
        symmetry: str = "",
        specificity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect fully general counterargument."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FULLY_GENERAL_COUNTERARGUMENT_PROMPT.format(
                argument=argument,
                target=target or "Not specified",
                symmetry=symmetry or "Not specified",
                specificity=specificity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FULLY_GENERAL_COUNTERARGUMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "fully_general_present": data.get("fully_general_present", False),
            "severity": data.get("severity", ""),
            "target_claim": data.get("target_claim", ""),
            "symmetry_test": data.get("symmetry_test", ""),
            "evidential_value": data.get("evidential_value", ""),
            "specificity": data.get("specificity", ""),
            "alternative_dismissal": data.get("alternative_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""ProvingTooMuchService — Proving Too Much Detection.

Detects "proving too much" — arguments whose logic, if valid,
would prove absurd or unwanted conclusions. If your argument
against X also proves against Y (which you accept), then your
argument is too strong — it proves more than you intended, which
means something is wrong with the argument's structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROVING_TOO_MUCH_SYSTEM = """You are a 'proving too much' specialist. Given an argument, assess whether its logic would prove absurd conclusions if applied consistently:

Key concepts:
- Proving too much: argument logic proves more than intended
- Reductio ad absurdum: following logic to absurd conclusions
- Overgeneralization: argument applies too broadly
- Selective application: using logic only where convenient
- Consistency test: does the arguer accept all implications?
- Scope creep of logic: argument covers cases it shouldn't
- Unintended consequences of reasoning: logic proves unwanted things

When proving too much IS present:
- "We shouldn't do X because it might fail" (proves against all action)
- "We can't trust Y because people are biased" (proves against all knowledge)
- "Technology Z is dangerous" with logic that applies to all technology
- Argument against one thing that equally argues against accepted things
- Logic that, if applied consistently, would paralyze all decision-making
- "Slippery slope" arguments that prove too much about any change
- Arguments whose premises, if true, would prove absurd conclusions

When the argument IS appropriately scoped:
- The logic applies specifically to the target and not to accepted cases
- The arguer can explain why the logic doesn't extend to absurd cases
- There are principled distinctions limiting the argument's scope
- The argument has been tested against edge cases
- The conclusion follows from premises without overgeneralization

Output JSON with: proving_too_much_present (bool), severity (none/mild/moderate/severe), argument (what argument is being made), intended_conclusion (what the arguer wants to prove), unintended_conclusions (what else the logic proves), absurd_implication (what absurd conclusion follows), scope_problem (why does the argument overshoot), consistency_check (does the arguer accept all implications), recommendation (argument_well_scoped/mild_overgeneralization/significant_proving_too_much/major_logic_overreach/narrow_argument_scope)."""

PROVING_TOO_MUCH_PROMPT = """Detect proving too much:

Argument: {argument}
Intended target: {target}
Logic used: {logic}
Other applications: {other_applications}
Domain: {domain}
Context: {context}

Would this argument's logic, if applied consistently, prove absurd or unwanted conclusions? Return ONLY valid JSON."""


class ProvingTooMuchService:
    """Detects proving too much — arguments whose logic proves absurd conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        target: str = "",
        logic: str = "",
        other_applications: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect proving too much."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROVING_TOO_MUCH_PROMPT.format(
                argument=argument,
                target=target or "Not specified",
                logic=logic or "Not specified",
                other_applications=other_applications or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROVING_TOO_MUCH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "proving_too_much_present": data.get("proving_too_much_present", False),
            "severity": data.get("severity", ""),
            "intended_conclusion": data.get("intended_conclusion", ""),
            "unintended_conclusions": data.get("unintended_conclusions", ""),
            "absurd_implication": data.get("absurd_implication", ""),
            "scope_problem": data.get("scope_problem", ""),
            "consistency_check": data.get("consistency_check", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EinstellungEffectService — Einstellung Effect Detection.

Detects Einstellung effect — when a known solution or familiar
approach prevents the discovery of a better, more efficient, or
more appropriate solution. Prior experience creates a mental set
that blocks creative problem-solving.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EINSTELLUNG_SYSTEM = """You are an Einstellung effect specialist. Given a problem-solving approach, assess whether familiarity with one solution is blocking discovery of a better one:

Key concepts:
- Einstellung effect: known solution blocks finding better one
- Mental set: habitual approach to problem-solving
- Functional fixedness: inability to see alternative uses
- Expert blind spot: expertise creating tunnel vision
- First-solution bias: accepting the first workable solution
- Satisficing vs optimizing: stopping at "good enough"
- Creative block: prior knowledge inhibiting novel approaches

When Einstellung effect IS present:
- Immediately jumping to a familiar solution without exploring
- "We solved a similar problem with X" without checking if X is optimal here
- Expert applying standard approach to a non-standard problem
- Failing to see a simpler solution because a complex one is known
- Pattern matching to familiar problems without verifying the match
- Resistance to novel approaches because the old way "works"
- Solving the problem you know how to solve, not the actual problem

When Einstellung effect is NOT present:
- Multiple approaches were considered before choosing
- The familiar solution was validated as optimal for this case
- Novel approaches were explored and found inferior
- The problem genuinely matches the pattern being applied
- The solver actively sought alternative framings
- Constraints were examined for creative solutions
- The familiar approach is genuinely the best fit

Output JSON with: einstellung_present (bool), severity (none/mild/moderate/severe), known_solution (what familiar approach is being applied), better_alternative (what better solution might exist), blocking_mechanism (how does familiarity block discovery), problem_fit (how well does the known solution actually fit), recommendation (no_einstellung/mild_fixation/significant_einstellung/major_solution_blocking/explore_alternatives)."""

EINSTELLUNG_PROMPT = """Detect Einstellung effect:

Approach: {approach}
Known solution: {known_solution}
Problem specifics: {problem}
Alternatives explored: {alternatives}
Domain: {domain}
Context: {context}

Is a known solution blocking discovery of a better one? Return ONLY valid JSON."""


class EinstellungEffectService:
    """Detects Einstellung effect — known solution blocking better alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        approach: str,
        *,
        known_solution: str = "",
        problem: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Einstellung effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EINSTELLUNG_PROMPT.format(
                approach=approach,
                known_solution=known_solution or "Not specified",
                problem=problem or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EINSTELLUNG_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "approach": approach[:200],
            "einstellung_present": data.get("einstellung_present", False),
            "severity": data.get("severity", ""),
            "known_solution": data.get("known_solution", ""),
            "better_alternative": data.get("better_alternative", ""),
            "blocking_mechanism": data.get("blocking_mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }

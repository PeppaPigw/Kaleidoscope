"""BeliefOverkillService — Belief Overkill Detection.

Detects belief overkill — marshaling every possible argument
for a position rather than focusing on the strongest ones.
Tetlock (2005). When people are committed to a conclusion,
they pile on arguments indiscriminately — weak, strong,
contradictory — rather than presenting the best case.
This actually weakens persuasion and signals motivated reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_OVERKILL_SYSTEM = """You are a belief overkill specialist. Given an argument or case being made, assess whether the arguer is piling on every possible reason rather than focusing on the strongest:

Key concepts (Tetlock, 2005):
- Belief overkill: using every argument regardless of quality
- Kitchen sink argumentation: throwing everything at the wall
- Argument dilution: weak arguments weakening the overall case
- Motivated reasoning signal: overkill signals conclusion-first thinking
- Quality vs quantity: fewer strong arguments beat many weak ones
- Contradictory arguments: using mutually exclusive reasons
- Defensive argumentation: anticipating every possible objection

When belief overkill IS present:
- Listing 10 reasons when 3 strong ones would be more persuasive
- Including weak or speculative arguments alongside strong ones
- Arguments that contradict each other (can't all be true simultaneously)
- "And another thing..." pattern of piling on
- Quantity of arguments substituting for quality of evidence
- Defensive exhaustiveness rather than focused persuasion
- Every possible angle covered regardless of strength

When comprehensive argumentation IS appropriate:
- The audience genuinely needs multiple independent lines of evidence
- Each argument addresses a different stakeholder's concern
- The arguments are all genuinely strong and non-redundant
- Completeness is required by the format (legal brief, systematic review)
- The arguments build on each other rather than just accumulating

Output JSON with: belief_overkill_present (bool), severity (none/mild/moderate/severe), argument (what case is being made), total_arguments (how many arguments are presented), strong_arguments (which arguments are genuinely strong), weak_arguments (which arguments are weak or speculative), contradictions (any mutually exclusive arguments), dilution_effect (how do weak arguments affect the overall case), recommendation (argumentation_appropriate/mild_over_arguing/significant_belief_overkill/major_kitchen_sink/focus_on_strongest_arguments)."""

BELIEF_OVERKILL_PROMPT = """Detect belief overkill:

Argument: {argument}
Reasons given: {reasons}
Strongest case: {strongest}
Weakest elements: {weakest}
Domain: {domain}
Context: {context}

Is the arguer piling on every possible reason rather than focusing on the strongest? Return ONLY valid JSON."""


class BeliefOverkillService:
    """Detects belief overkill — marshaling every argument rather than the strongest."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        reasons: str = "",
        strongest: str = "",
        weakest: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief overkill."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_OVERKILL_PROMPT.format(
                argument=argument,
                reasons=reasons or "Not specified",
                strongest=strongest or "Not specified",
                weakest=weakest or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_OVERKILL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "belief_overkill_present": data.get("belief_overkill_present", False),
            "severity": data.get("severity", ""),
            "total_arguments": data.get("total_arguments", ""),
            "strong_arguments": data.get("strong_arguments", ""),
            "weak_arguments": data.get("weak_arguments", ""),
            "contradictions": data.get("contradictions", ""),
            "dilution_effect": data.get("dilution_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }

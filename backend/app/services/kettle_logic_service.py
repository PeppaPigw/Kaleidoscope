"""KettleLogicService — Kettle Logic Detection.

Detects kettle logic — using multiple inconsistent arguments to
defend the same conclusion. Named after Freud's example: "I never
borrowed your kettle; it was already broken when I got it; and I
returned it in perfect condition." Each defense contradicts the others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KETTLE_LOGIC_SYSTEM = """You are a kettle logic specialist. Given a defense or argument, assess whether multiple inconsistent justifications are being used simultaneously:

Key concepts (Freud/Derrida):
- Kettle logic: multiple contradictory defenses for same conclusion
- Internal inconsistency: arguments contradict each other
- Overdetermination: too many incompatible reasons offered
- Shotgun argumentation: throwing everything at the wall
- Logical incompatibility: accepting one defense negates another
- Defensive layering: each layer contradicts the previous
- Implicit admission: the contradictions reveal the weakness

When kettle logic IS present:
- "I didn't do it; and if I did, it wasn't wrong; and if it was, it wasn't my fault"
- Multiple defenses that can't all be true simultaneously
- Shifting between contradictory explanations
- Each argument implicitly admits the failure of the previous one
- The defenses work individually but are incompatible together
- Overdetermined justification that reveals desperation
- "It didn't happen / it wasn't that bad / they deserved it"

When multiple arguments ARE appropriate:
- The arguments are consistent with each other (alternative, not contradictory)
- They address different aspects of the criticism
- They are presented as "even if" chains that build on each other
- The speaker acknowledges which arguments are alternatives
- Disjunctive reasoning: "either A or B, and in both cases..."
- The arguments are genuinely independent and compatible
- Uncertainty about which defense applies (acknowledged)

Output JSON with: kettle_logic_present (bool), severity (none/mild/moderate/severe), conclusion (what is being defended), arguments (list of defenses offered), contradictions (which arguments contradict each other), implicit_admissions (what does each argument implicitly admit), recommendation (arguments_consistent/mild_tension/significant_kettle_logic/major_self_contradiction/choose_strongest_argument)."""

KETTLE_LOGIC_PROMPT = """Detect kettle logic:

Defense: {defense}
Arguments: {arguments}
Conclusion: {conclusion}
Consistency: {consistency}
Domain: {domain}
Context: {context}

Are multiple inconsistent arguments being used to defend the same conclusion? Return ONLY valid JSON."""


class KettleLogicService:
    """Detects kettle logic — multiple contradictory defenses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        defense: str,
        *,
        arguments: str = "",
        conclusion: str = "",
        consistency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect kettle logic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KETTLE_LOGIC_PROMPT.format(
                defense=defense,
                arguments=arguments or "Not specified",
                conclusion=conclusion or "Not specified",
                consistency=consistency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KETTLE_LOGIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "defense": defense[:200],
            "kettle_logic_present": data.get("kettle_logic_present", False),
            "severity": data.get("severity", ""),
            "arguments": data.get("arguments", ""),
            "contradictions": data.get("contradictions", ""),
            "implicit_admissions": data.get("implicit_admissions", ""),
            "recommendation": data.get("recommendation", ""),
        }

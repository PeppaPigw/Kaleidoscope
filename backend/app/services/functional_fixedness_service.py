"""FunctionalFixednessService — Functional Fixedness Detection.

Detects functional fixedness — inability to see an object or
concept beyond its traditional use. Duncker (1945). The candle
problem. Prevents creative problem-solving by constraining
solution space to conventional applications. "A hammer is only
for nails" thinking blocks innovation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FUNCTIONAL_FIXEDNESS_SYSTEM = """You are a functional fixedness specialist. Given a problem-solving situation, assess whether the solver is constrained by conventional uses of available resources:

Key concepts (Duncker, 1945):
- Functional fixedness: inability to use objects in novel ways
- Design fixation: being stuck on existing design solutions
- Einstellung effect: using familiar methods when better ones exist
- Mental set: approaching problems with habitual strategies
- Constraint relaxation: removing assumed limitations
- Analogical transfer: applying solutions from other domains
- Repurposing: using existing resources in unconventional ways

When functional fixedness IS present:
- Only considering conventional uses of available tools/resources
- "We can't do X because we don't have Y" when existing resources could work
- Failing to see alternative applications of existing capabilities
- Stuck on the "intended" use of a tool, system, or process
- Not considering repurposing, combining, or adapting what's available
- Seeking new resources when existing ones could be reconfigured

When the conventional approach IS appropriate:
- The conventional use is genuinely optimal for this situation
- Alternative uses would be unreliable or risky
- The problem genuinely requires specialized tools not available
- Time constraints make creative solutions impractical
- The "fixedness" is actually appropriate domain expertise

Output JSON with: functional_fixedness_present (bool), severity (none/mild/moderate/severe), problem (what problem is being solved), fixed_object (what is being seen only in its conventional role), conventional_use (the traditional use being assumed), alternative_uses (potential unconventional applications), constraints_assumed (what limitations are being assumed?), constraints_real (which constraints are actually real?), available_resources (what resources could be repurposed?), creative_solutions (what solutions become possible without fixedness?), domain_transfer (solutions from analogous domains?), recommendation (conventional_approach_optimal/mild_fixedness/significant_constraint/major_creative_block/reframe_available_resources)."""

FUNCTIONAL_FIXEDNESS_PROMPT = """Detect functional fixedness:

Problem: {problem}
Available resources: {resources}
Attempted solutions: {attempts}
Constraints: {constraints}
Domain: {domain}
Context: {context}

Is the solver constrained by conventional uses of available resources? Return ONLY valid JSON."""


class FunctionalFixednessService:
    """Detects functional fixedness — inability to see beyond conventional uses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        problem: str,
        *,
        resources: str = "",
        attempts: str = "",
        constraints: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect functional fixedness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FUNCTIONAL_FIXEDNESS_PROMPT.format(
                problem=problem,
                resources=resources or "Not specified",
                attempts=attempts or "Not specified",
                constraints=constraints or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FUNCTIONAL_FIXEDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "functional_fixedness_present": data.get("functional_fixedness_present", False),
            "severity": data.get("severity", ""),
            "fixed_object": data.get("fixed_object", ""),
            "conventional_use": data.get("conventional_use", ""),
            "alternative_uses": data.get("alternative_uses", ""),
            "constraints_assumed": data.get("constraints_assumed", ""),
            "constraints_real": data.get("constraints_real", ""),
            "available_resources": data.get("available_resources", ""),
            "creative_solutions": data.get("creative_solutions", ""),
            "domain_transfer": data.get("domain_transfer", ""),
            "recommendation": data.get("recommendation", ""),
        }

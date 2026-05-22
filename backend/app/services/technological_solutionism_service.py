"""TechnologicalSolutionismService — Technological Solutionism Detection.

Detects technological solutionism — the assumption that every problem
has a technological solution, and that technology is always the best
approach. Evgeny Morozov (2013). Reframes complex social, political,
and human problems as engineering problems with clean technical fixes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TECH_SOLUTIONISM_SYSTEM = """You are a technological solutionism specialist. Given a proposed solution, assess whether it inappropriately assumes technology is the answer to a fundamentally non-technical problem:

Key concepts (Morozov, 2013):
- Technological solutionism: assuming all problems have tech solutions
- Problem reframing: redefining social problems as engineering problems
- Techno-utopianism: technology as salvation narrative
- Complexity denial: ignoring social/political dimensions
- App-for-that thinking: every problem needs a digital solution
- Quantification bias: if you can't measure it, it doesn't exist
- Efficiency fetishism: optimizing the wrong thing

When solutionism IS present:
- Complex social problems reduced to "we need an app for that"
- Political problems reframed as information/efficiency problems
- Human judgment replaced by algorithms without considering tradeoffs
- Technology proposed without addressing root causes
- "If only we had better data/AI/platform" for fundamentally human problems
- Ignoring that the problem is political, not technical
- Assuming technology is neutral and will be used as intended

When technology IS appropriate:
- The problem genuinely has a technical component
- Technology addresses root causes, not just symptoms
- Social and political dimensions are also addressed
- The solution accounts for how technology will actually be used
- Non-technical alternatives were considered and found insufficient
- The technology empowers rather than replaces human judgment
- Implementation challenges are acknowledged

Output JSON with: solutionism_present (bool), severity (none/mild/moderate/severe), problem (what problem is being addressed), proposed_solution (what technology is proposed), non_technical_dimensions (what social/political aspects are ignored), root_cause (what is the actual root cause), alternative_approaches (what non-tech approaches exist), recommendation (technology_appropriate/mild_tech_bias/significant_solutionism/major_problem_reframing/address_root_causes)."""

TECH_SOLUTIONISM_PROMPT = """Detect technological solutionism:

Problem: {problem}
Proposed solution: {solution}
Non-technical dimensions: {dimensions}
Root cause: {root_cause}
Domain: {domain}
Context: {context}

Is technology being inappropriately assumed as the solution to a fundamentally non-technical problem? Return ONLY valid JSON."""


class TechnologicalSolutionismService:
    """Detects technological solutionism — assuming tech solves everything."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        problem: str,
        *,
        solution: str = "",
        dimensions: str = "",
        root_cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect technological solutionism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TECH_SOLUTIONISM_PROMPT.format(
                problem=problem,
                solution=solution or "Not specified",
                dimensions=dimensions or "Not specified",
                root_cause=root_cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TECH_SOLUTIONISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "solutionism_present": data.get("solutionism_present", False),
            "severity": data.get("severity", ""),
            "non_technical_dimensions": data.get("non_technical_dimensions", ""),
            "root_cause": data.get("root_cause", ""),
            "alternative_approaches": data.get("alternative_approaches", ""),
            "recommendation": data.get("recommendation", ""),
        }

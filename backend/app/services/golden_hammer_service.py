"""GoldenHammerService — Golden Hammer Detection.

Detects golden hammer (law of the instrument) — treating a
familiar tool, technique, or approach as the solution to every
problem. "If all you have is a hammer, everything looks like
a nail." Over-reliance on familiar solutions prevents finding
better-suited approaches.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOLDEN_HAMMER_SYSTEM = """You are a golden hammer specialist. Given a proposed solution, assess whether it reflects over-reliance on a familiar tool rather than fitness for the problem:

Key concepts:
- Law of the instrument: familiar tools applied to all problems
- Maslow's hammer: "if all you have is a hammer..."
- Tool bias: preferring known tools over better-suited ones
- Expertise trap: deep expertise in X makes everything look like X
- Solution-first thinking: starting with the tool, not the problem
- Technology fetishism: using tech because it's known, not because it fits
- Appropriate technology: matching tools to problems

When golden hammer IS present:
- Using the same framework/language/approach for every project
- "We should use X" before understanding the problem
- Forcing a problem to fit a familiar solution
- Ignoring better-suited alternatives because they're unfamiliar
- "We've always used X" as justification for using X again
- Expertise in a tool driving problem framing
- Rejecting alternatives without evaluation

When golden hammer is NOT present:
- The tool is genuinely well-suited to the problem
- Alternatives were considered and the familiar tool won on merit
- The problem naturally fits the proposed solution
- Familiarity is one factor among many (team expertise, ecosystem)
- The choice acknowledges tradeoffs
- The tool's limitations for this use case are discussed
- Problem-first thinking led to the familiar tool

Output JSON with: golden_hammer_present (bool), severity (none/mild/moderate/severe), tool (what familiar tool is proposed), problem (what problem needs solving), fitness (how well does the tool fit), alternatives (what better-suited options exist), recommendation (no_golden_hammer/mild_tool_bias/significant_golden_hammer/major_solution_forcing/evaluate_alternatives)."""

GOLDEN_HAMMER_PROMPT = """Detect golden hammer:

Proposal: {proposal}
Tool/approach: {tool}
Problem: {problem}
Alternatives considered: {alternatives}
Domain: {domain}
Context: {context}

Is a familiar tool being applied regardless of fitness for the problem? Return ONLY valid JSON."""


class GoldenHammerService:
    """Detects golden hammer — over-reliance on familiar tools."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proposal: str,
        *,
        tool: str = "",
        problem: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect golden hammer."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOLDEN_HAMMER_PROMPT.format(
                proposal=proposal,
                tool=tool or "Not specified",
                problem=problem or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GOLDEN_HAMMER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proposal": proposal[:200],
            "golden_hammer_present": data.get("golden_hammer_present", False),
            "severity": data.get("severity", ""),
            "tool": data.get("tool", ""),
            "problem": data.get("problem", ""),
            "alternatives": data.get("alternatives", ""),
            "recommendation": data.get("recommendation", ""),
        }

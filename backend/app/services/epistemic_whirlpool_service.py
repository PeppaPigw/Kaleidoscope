"""EpistemicWhirlpoolService — Epistemic Whirlpool Detection.

Detects epistemic whirlpools — circular reasoning patterns that
pull in and trap nearby ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WHIRLPOOL_SYSTEM = """You are an epistemic whirlpool specialist. Given a reasoning pattern, assess whether circular logic is pulling in and trapping nearby ideas:

Key concepts:
- Epistemic whirlpool: circular reasoning pulling in ideas
- Circular trap: circular logic trapping thought
- Idea capture: nearby ideas pulled into circular pattern
- Reasoning vortex: vortex of circular reasoning
- Escape difficulty: difficulty escaping circular pattern
- Gravitational pull: circular reasoning pulling in related ideas
- Progressive entrapment: more ideas trapped over time

When epistemic whirlpool IS present:
- Circular reasoning pulling in nearby ideas
- Circular logic trapping thought in loops
- Nearby ideas pulled into circular pattern
- Vortex of circular reasoning growing
- Difficulty escaping circular pattern
- Circular reasoning pulling in related ideas
- More ideas trapped over time

When focused iteration is present:
- Iterative reasoning making progress
- Revisiting ideas with new insight each time
- Related ideas enriching rather than trapped
- Iteration deepening understanding
- Easy to step out when needed
- Focus productive rather than trapping
- Each iteration advancing understanding

Output JSON with: whirlpool_present (bool), severity (none/mild/moderate/severe), pattern (what pattern exists), circularity (what circular reasoning exists), captured (what ideas are captured), escape (how difficult escape is), recommendation (focused_iteration/mild_circularity/significant_whirlpool/major_reasoning_vortex/break_circular_pattern)."""

EPISTEMIC_WHIRLPOOL_PROMPT = """Detect epistemic whirlpool:

Pattern: {pattern}
Circularity: {circularity}
Captured: {captured}
Escape: {escape}
Domain: {domain}
Context: {context}

Is circular reasoning pulling in and trapping nearby ideas? Return ONLY valid JSON."""


class EpistemicWhirlpoolService:
    """Detects epistemic whirlpools — circular reasoning trapping ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        circularity: str = "",
        captured: str = "",
        escape: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic whirlpool."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WHIRLPOOL_PROMPT.format(
                pattern=pattern,
                circularity=circularity or "Not specified",
                captured=captured or "Not specified",
                escape=escape or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WHIRLPOOL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "whirlpool_present": data.get("whirlpool_present", False),
            "severity": data.get("severity", ""),
            "circularity": data.get("circularity", ""),
            "captured": data.get("captured", ""),
            "escape": data.get("escape", ""),
            "recommendation": data.get("recommendation", ""),
        }

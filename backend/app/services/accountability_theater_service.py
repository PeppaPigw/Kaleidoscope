"""AccountabilityTheaterService — Accountability Theater Detection.

Detects accountability theater — when accountability mechanisms
become performative rather than functional, creating the appearance
of oversight without actual consequence or learning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACCOUNTABILITY_THEATER_SYSTEM = """You are an accountability theater specialist. Given an accountability situation, assess whether mechanisms are performative rather than functional:

Key concepts:
- Accountability theater: appearance of oversight without substance
- Performative compliance: going through motions without effect
- Toothless oversight: review without consequence
- Blame ritual: assigning blame without changing systems
- Report filing: producing reports nobody reads or acts on
- Audit theater: audits that never find problems
- Lessons identified vs lessons learned: identifying without implementing

When accountability theater IS present:
- Accountability mechanisms exist but have no consequences
- Reviews conducted but findings never implemented
- Reports produced but never read or acted upon
- Oversight bodies lack power or independence
- Same problems recur despite accountability processes
- Blame assigned but systems unchanged
- Compliance checked but effectiveness not measured

When accountability is functional:
- Mechanisms have real consequences
- Findings lead to actual changes
- Reports inform decisions
- Oversight bodies have independence and power
- Problems addressed when identified
- Systems changed based on accountability findings
- Learning actually occurs from review processes

Output JSON with: theater_present (bool), severity (none/mild/moderate/severe), mechanism (what accountability mechanism), performance (what performative elements exist), consequences (whether real consequences follow), learning (whether actual learning occurs), recommendation (functional_accountability/mild_theater/significant_performative/major_accountability_theater/add_real_consequences)."""

ACCOUNTABILITY_THEATER_PROMPT = """Detect accountability theater:

Situation: {situation}
Mechanism: {mechanism}
Consequences: {consequences}
Changes made: {changes}
Domain: {domain}
Context: {context}

Are accountability mechanisms performative rather than functional? Return ONLY valid JSON."""


class AccountabilityTheaterService:
    """Detects accountability theater — performative oversight without substance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        mechanism: str = "",
        consequences: str = "",
        changes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect accountability theater."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACCOUNTABILITY_THEATER_PROMPT.format(
                situation=situation,
                mechanism=mechanism or "Not specified",
                consequences=consequences or "Not specified",
                changes=changes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACCOUNTABILITY_THEATER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "theater_present": data.get("theater_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "performance": data.get("performance", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }

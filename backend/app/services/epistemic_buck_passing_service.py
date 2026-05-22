"""EpistemicBuckPassingService — Epistemic Buck Passing Detection.

Detects epistemic buck passing — passing responsibility for knowing
to others when one should know oneself, where epistemic duty
is deflected rather than fulfilled.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BUCK_PASSING_SYSTEM = """You are an epistemic buck passing specialist. Given a knowledge responsibility situation, assess whether epistemic duty is being deflected:

Key concepts:
- Epistemic buck passing: deflecting duty to know
- Knowledge responsibility deflection: passing knowing to others
- Duty to inquire avoidance: not investigating when one should
- Epistemic delegation without justification: others expected to know
- Willful delegation: choosing not to know by delegating
- Responsibility gap: no one taking epistemic responsibility
- Accountability deflection: blame for not knowing passed around

When epistemic buck passing IS present:
- Responsibility for knowing deflected to others
- Duty to inquire avoided through delegation
- No one taking ownership of epistemic responsibility
- Knowledge gaps maintained by passing responsibility
- Accountability for not knowing deflected
- Epistemic duty recognized but not fulfilled
- Others expected to know what one should know oneself

When appropriate delegation is present:
- Delegation based on genuine expertise differences
- Responsibility clearly assigned and accepted
- Delegator maintains oversight responsibility
- Epistemic duty fulfilled through appropriate channels
- Accountability clear even when delegated
- Knowledge responsibility proportionate to role
- Delegation serving rather than avoiding epistemic duty

Output JSON with: buck_passing_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), responsibility (what epistemic responsibility exists), deflection (how responsibility is deflected), gap (what knowledge gap results), recommendation (appropriate_delegation/mild_responsibility_avoidance/significant_buck_passing/major_epistemic_duty_deflection/accept_epistemic_responsibility)."""

EPISTEMIC_BUCK_PASSING_PROMPT = """Detect epistemic buck passing:

Situation: {situation}
Knowledge needed: {knowledge}
Responsibility claimed: {claimed}
Responsibility deflected: {deflected}
Domain: {domain}
Context: {context}

Is epistemic responsibility being passed to others when one should know oneself? Return ONLY valid JSON."""


class EpistemicBuckPassingService:
    """Detects epistemic buck passing — deflecting duty to know."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        claimed: str = "",
        deflected: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic buck passing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BUCK_PASSING_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                claimed=claimed or "Not specified",
                deflected=deflected or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BUCK_PASSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "buck_passing_present": data.get("buck_passing_present", False),
            "severity": data.get("severity", ""),
            "responsibility": data.get("responsibility", ""),
            "deflection": data.get("deflection", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }

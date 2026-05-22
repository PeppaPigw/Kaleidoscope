"""IsolatedDemandPerfectionService — Isolated Demand for Perfection Detection.

Detects isolated demand for perfection — rejecting a solution because
it doesn't solve every aspect of a problem, while accepting the status
quo which solves none. A proposal is held to an impossible standard
while the alternative (doing nothing) faces no scrutiny at all.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ISOLATED_DEMAND_PERFECTION_SYSTEM = """You are an isolated demand for perfection specialist. Given a proposal evaluation, assess whether a solution is being rejected for not being perfect while the status quo faces no such scrutiny:

Key concepts:
- Isolated demand for perfection: rejecting imperfect solutions while tolerating worse status quo
- Nirvana fallacy overlap: comparing real proposals to ideal rather than to alternatives
- Asymmetric scrutiny: proposed changes face higher bar than current state
- Perfect as enemy of good: refusing improvement because it isn't complete
- Status quo privilege: existing state exempt from the standards applied to proposals
- Moving goalposts: raising standards as each is met
- Impossible standard: requiring a solution to solve all problems simultaneously

When isolated demand for perfection IS present:
- A proposal is rejected for not solving 100% of the problem
- The status quo (which solves 0%) faces no equivalent criticism
- Standards applied to the proposal would also disqualify the current approach
- "But it doesn't address X" when X isn't addressed now either
- Requiring a solution to have zero downsides while tolerating current downsides
- Holding proposals to standards that nothing could meet
- Rejecting incremental improvement because it isn't total transformation

When high standards ARE appropriate:
- The proposal genuinely introduces new risks not present in status quo
- The domain requires high confidence before changes (medicine, safety)
- The criticism identifies a fatal flaw, not just incompleteness
- The same standards are applied to all options including doing nothing
- The proposal claims to be complete but isn't
- Resources are limited and partial solutions waste them

Output JSON with: isolated_demand_perfection_present (bool), severity (none/mild/moderate/severe), proposal (what is being proposed), criticism (what criticism is being leveled), status_quo (what is the current state), asymmetry (how are standards applied differently), improvement (how much would the proposal improve things), recommendation (high_standards_appropriate/mild_perfectionism/significant_asymmetric_scrutiny/major_perfection_demand/evaluate_against_alternatives_not_ideals)."""

ISOLATED_DEMAND_PERFECTION_PROMPT = """Detect isolated demand for perfection:

Proposal: {proposal}
Criticism: {criticism}
Status quo: {status_quo}
Standards applied: {standards}
Domain: {domain}
Context: {context}

Is this proposal being rejected for imperfection while the status quo faces no equivalent scrutiny? Return ONLY valid JSON."""


class IsolatedDemandPerfectionService:
    """Detects isolated demand for perfection — rejecting imperfect solutions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proposal: str,
        *,
        criticism: str = "",
        status_quo: str = "",
        standards: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect isolated demand for perfection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ISOLATED_DEMAND_PERFECTION_PROMPT.format(
                proposal=proposal,
                criticism=criticism or "Not specified",
                status_quo=status_quo or "Not specified",
                standards=standards or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ISOLATED_DEMAND_PERFECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proposal": proposal[:200],
            "isolated_demand_perfection_present": data.get("isolated_demand_perfection_present", False),
            "severity": data.get("severity", ""),
            "criticism": data.get("criticism", ""),
            "status_quo": data.get("status_quo", ""),
            "asymmetry": data.get("asymmetry", ""),
            "improvement": data.get("improvement", ""),
            "recommendation": data.get("recommendation", ""),
        }

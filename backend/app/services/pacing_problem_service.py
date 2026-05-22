"""PacingProblemService — Pacing Problem Detection.

Detects pacing problem — technology advancing faster than governance,
regulation, or social norms can adapt. The gap between technological
capability and institutional response creates a governance vacuum
where harms can accumulate before rules catch up.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PACING_PROBLEM_SYSTEM = """You are a pacing problem specialist. Given a technology-governance dynamic, assess whether technology is outpacing the ability of institutions to respond:

Key concepts:
- Pacing problem: technology faster than governance
- Governance vacuum: period where no rules apply to new capabilities
- Regulatory lag: time between technology deployment and regulation
- Innovation vs. precaution: speed of development vs. speed of oversight
- Permissionless innovation: deploying first, asking forgiveness later
- Institutional capacity: can regulators even understand the technology?
- Anticipatory governance: trying to govern before problems manifest

When pacing problem IS present:
- Technology is deployed with no applicable regulatory framework
- Regulators lack technical understanding to create appropriate rules
- Harms accumulate during the governance gap
- "Move fast and break things" in domains with real consequences
- Existing regulations are clearly inadequate for new capabilities
- By the time rules are made, the technology has moved on
- Governance is always one generation behind the technology

When pace IS appropriate:
- The technology operates within existing regulatory frameworks
- Self-regulation is effective and accountable
- The governance gap is acknowledged and actively managed
- Harm is minimal during the transition period
- Regulatory sandboxes allow controlled experimentation
- The technology community engages proactively with governance
- Adaptive regulation keeps pace with development

Output JSON with: pacing_problem_present (bool), severity (none/mild/moderate/severe), technology (what technology), governance (what governance exists), gap (how large is the gap), harms (what harms accumulate in the gap), institutional_capacity (can institutions respond), recommendation (pace_appropriate/mild_lag/significant_pacing_problem/major_governance_vacuum/accelerate_governance_or_slow_deployment)."""

PACING_PROBLEM_PROMPT = """Detect pacing problem:

Technology: {technology}
Governance: {governance}
Gap: {gap}
Harms: {harms}
Domain: {domain}
Context: {context}

Is technology advancing faster than governance can adapt, creating a harmful vacuum? Return ONLY valid JSON."""


class PacingProblemService:
    """Detects pacing problem — technology outpacing governance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        technology: str,
        *,
        governance: str = "",
        gap: str = "",
        harms: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect pacing problem."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PACING_PROBLEM_PROMPT.format(
                technology=technology,
                governance=governance or "Not specified",
                gap=gap or "Not specified",
                harms=harms or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PACING_PROBLEM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "technology": technology[:200],
            "pacing_problem_present": data.get("pacing_problem_present", False),
            "severity": data.get("severity", ""),
            "gap": data.get("gap", ""),
            "harms": data.get("harms", ""),
            "institutional_capacity": data.get("institutional_capacity", ""),
            "recommendation": data.get("recommendation", ""),
        }

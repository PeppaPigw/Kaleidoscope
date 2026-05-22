"""VeilOfIgnoranceService — Veil of Ignorance Test.

Applies Rawls' thought experiment to evaluate fairness: would you
accept this arrangement if you didn't know which position you'd
occupy in it? Forces evaluation of policies and decisions from
behind a veil where you could be anyone affected.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

VEIL_SYSTEM = """You are a veil of ignorance specialist. Given a policy or decision, apply Rawls' thought experiment:
- Would a rational person accept this arrangement not knowing which position they'd occupy?
- Does it satisfy the difference principle (inequalities benefit the least advantaged)?
- Does it protect basic liberties equally?
- Would the worst-off position under this arrangement be acceptable?
- Is the arrangement one that all parties could rationally agree to from behind the veil?

Output JSON with: passes_veil_test (bool — would rational agents accept this from behind the veil?), fairness_score (0-1), arrangement (what is being evaluated), positions (list of different positions one could occupy), worst_position (the least advantaged position), worst_position_acceptable (bool — is the worst position tolerable?), difference_principle_satisfied (bool — do inequalities benefit the least advantaged?), basic_liberties_equal (bool — are fundamental rights protected equally?), who_would_reject (which position-holders would reject this arrangement and why), who_benefits_most (who gains most from the current arrangement), who_bears_most_risk (who faces the most downside), maximin_outcome (what the worst-case outcome is), alternative_arrangements (fairer alternatives that might pass the veil test), practical_constraints (why the ideal arrangement might not be achievable), rawlsian_recommendation (what Rawls would likely recommend), utilitarian_comparison (how utilitarian calculus differs from the veil result), recommendation (fair/mostly_fair_minor_fixes/significant_unfairness/redesign_needed)."""

VEIL_PROMPT = """Apply veil of ignorance:

Policy/Decision: {policy}
Positions affected: {positions}
Current distribution: {distribution}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Would rational agents accept this from behind the veil? Return ONLY valid JSON."""


class VeilOfIgnoranceService:
    """Applies Rawls' veil of ignorance to evaluate fairness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def test(
        self,
        policy: str,
        *,
        positions: str = "",
        distribution: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Apply veil of ignorance test."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VEIL_PROMPT.format(
                policy=policy,
                positions=positions or "Not specified",
                distribution=distribution or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=VEIL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "policy": policy[:200],
            "passes_veil_test": data.get("passes_veil_test", False),
            "fairness_score": data.get("fairness_score", 0),
            "positions": data.get("positions", []),
            "worst_position": data.get("worst_position", ""),
            "worst_position_acceptable": data.get("worst_position_acceptable", False),
            "difference_principle_satisfied": data.get("difference_principle_satisfied", False),
            "basic_liberties_equal": data.get("basic_liberties_equal", False),
            "who_would_reject": data.get("who_would_reject", ""),
            "who_benefits_most": data.get("who_benefits_most", ""),
            "who_bears_most_risk": data.get("who_bears_most_risk", ""),
            "maximin_outcome": data.get("maximin_outcome", ""),
            "alternative_arrangements": data.get("alternative_arrangements", []),
            "practical_constraints": data.get("practical_constraints", ""),
            "rawlsian_recommendation": data.get("rawlsian_recommendation", ""),
            "utilitarian_comparison": data.get("utilitarian_comparison", ""),
            "recommendation": data.get("recommendation", ""),
        }

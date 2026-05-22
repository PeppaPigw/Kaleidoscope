"""NotInventedHereService — Not-Invented-Here Syndrome Detection.

Detects Not-Invented-Here (NIH) syndrome — the tendency to reject
external ideas, solutions, or technologies simply because they
weren't created internally. Leads to reinventing the wheel,
wasted resources, and missed opportunities for collaboration.
Katz & Allen (1982).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NIH_SYSTEM = """You are a Not-Invented-Here syndrome specialist. Given a decision about adopting or rejecting an external solution, assess whether NIH syndrome is distorting the evaluation:

Key concepts (Katz & Allen, 1982):
- NIH syndrome: rejecting external solutions because they weren't created here
- Pride of authorship: preferring own work regardless of quality
- Reinventing the wheel: building from scratch when good solutions exist
- Ego investment: identity tied to creating rather than selecting
- Control illusion: belief that internal solutions are more controllable
- Sunk cost in existing approach: reluctance to abandon internal work

When NIH IS present:
- External solutions dismissed without fair evaluation
- "We can build it better" without evidence
- Legitimate external options not seriously considered
- Internal solution preferred despite being inferior
- Rejection reasons are post-hoc rationalizations

When building internally IS appropriate:
- Genuine unique requirements that external solutions don't meet
- Critical competitive advantage that shouldn't be outsourced
- External solutions have real quality/security/reliability concerns
- Integration costs genuinely exceed build costs
- Strategic capability that must be owned

Output JSON with: nih_present (bool), severity (none/mild/moderate/severe), external_solution (what external option exists), internal_preference (what's being built/preferred instead), rejection_reasons (stated reasons for rejecting external), reasons_legitimate (bool — are the rejection reasons genuine?), fair_evaluation_done (bool — was the external option seriously assessed?), reinvention_cost (what building internally will cost), adoption_cost (what adopting external would cost), quality_comparison (how do the options actually compare?), ego_investment (bool — is pride driving the decision?), control_illusion (bool — false belief that internal = more controllable?), strategic_justification (is there a real strategic reason to build?), opportunity_cost (what else could be done with the resources), sunk_cost_factor (bool — is existing internal work biasing the decision?), recommendation (build_justified/mild_nih_bias/significant_nih_syndrome/major_reinvention_waste/adopt_external)."""

NIH_PROMPT = """Detect Not-Invented-Here syndrome:

Decision: {decision}
External option: {external_option}
Internal preference: {internal_preference}
Rejection reasons: {rejection_reasons}
Domain: {domain}
Context: {context}

Is NIH syndrome distorting this build-vs-adopt decision? Return ONLY valid JSON."""


class NotInventedHereService:
    """Detects Not-Invented-Here syndrome — rejecting external solutions without fair evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        external_option: str = "",
        internal_preference: str = "",
        rejection_reasons: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect NIH syndrome."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NIH_PROMPT.format(
                decision=decision,
                external_option=external_option or "Not specified",
                internal_preference=internal_preference or "Not specified",
                rejection_reasons=rejection_reasons or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NIH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "nih_present": data.get("nih_present", False),
            "severity": data.get("severity", ""),
            "external_solution": data.get("external_solution", ""),
            "internal_preference": data.get("internal_preference", ""),
            "rejection_reasons": data.get("rejection_reasons", ""),
            "reasons_legitimate": data.get("reasons_legitimate", False),
            "fair_evaluation_done": data.get("fair_evaluation_done", False),
            "reinvention_cost": data.get("reinvention_cost", ""),
            "adoption_cost": data.get("adoption_cost", ""),
            "quality_comparison": data.get("quality_comparison", ""),
            "ego_investment": data.get("ego_investment", False),
            "control_illusion": data.get("control_illusion", False),
            "strategic_justification": data.get("strategic_justification", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "sunk_cost_factor": data.get("sunk_cost_factor", False),
            "recommendation": data.get("recommendation", ""),
        }

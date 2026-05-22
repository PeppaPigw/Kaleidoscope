"""ZeroRiskService — Zero-Risk Bias Detection.

Detects zero-risk bias — preferring to eliminate a small risk
entirely rather than achieving a larger overall risk reduction.
Baron, Gowda & Kunreuther (1993). People prefer certainty of
zero risk in one area over a larger but incomplete reduction
across multiple areas. "Eliminate this 1% risk" vs "reduce
that 10% risk to 3%."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ZERO_RISK_SYSTEM = """You are a zero-risk bias specialist. Given a risk management decision, assess whether the preference for eliminating a small risk entirely is suboptimal compared to larger overall risk reduction:

Key concepts (Baron, Gowda & Kunreuther, 1993):
- Zero-risk bias: preferring complete elimination of one risk over larger total reduction
- Certainty effect overlap: disproportionate value placed on certainty (0% vs small%)
- Pseudocertainty: the "zero" may not actually be zero when examined closely
- Opportunity cost: resources spent on zero-risk could achieve more elsewhere
- Emotional appeal of "zero": the psychological comfort of complete elimination
- Risk compensation: eliminating one risk may increase risk-taking elsewhere

When zero-risk bias IS present:
- Choosing to eliminate a small risk entirely over reducing a larger risk significantly
- Disproportionate resources allocated to achieve "zero" in one area
- Ignoring the opportunity cost of complete elimination
- Emotional attachment to the concept of "zero risk"
- Refusing partial solutions that would save more lives/money overall
- "We must eliminate this completely" when reduction would be more efficient

When zero-risk preference IS rational:
- The risk is catastrophic (nuclear, existential) where any occurrence is unacceptable
- Regulatory or legal requirements mandate zero tolerance
- The cost of elimination is genuinely low relative to the benefit
- The "zero" creates important signaling or trust effects
- Partial reduction is genuinely not feasible (all-or-nothing intervention)

Output JSON with: zero_risk_present (bool), severity (none/mild/moderate/severe), risk_targeted (what risk is being eliminated), risk_level (how large is the targeted risk), alternative_reduction (what larger reduction is being foregone), total_risk_comparison (overall risk with each approach), certainty_appeal (how much is "zero" driving the preference?), opportunity_cost (what could the resources achieve elsewhere?), emotional_vs_rational (is the preference emotional or calculated?), pseudocertainty (bool — is the "zero" actually zero?), catastrophic_risk (bool — is any occurrence truly unacceptable?), cost_effectiveness (which approach saves more per unit cost?), recommendation (zero_risk_justified/mild_zero_risk_bias/significant_zero_risk_bias/major_misallocation/optimize_total_reduction)."""

ZERO_RISK_PROMPT = """Detect zero-risk bias:

Decision: {decision}
Risk being eliminated: {risk}
Alternative approach: {alternative}
Resources available: {resources}
Domain: {domain}
Context: {context}

Is the preference for zero risk suboptimal compared to larger overall reduction? Return ONLY valid JSON."""


class ZeroRiskService:
    """Detects zero-risk bias — preferring elimination over larger total reduction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        risk: str = "",
        alternative: str = "",
        resources: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect zero-risk bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ZERO_RISK_PROMPT.format(
                decision=decision,
                risk=risk or "Not specified",
                alternative=alternative or "Not specified",
                resources=resources or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ZERO_RISK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "zero_risk_present": data.get("zero_risk_present", False),
            "severity": data.get("severity", ""),
            "risk_targeted": data.get("risk_targeted", ""),
            "risk_level": data.get("risk_level", ""),
            "alternative_reduction": data.get("alternative_reduction", ""),
            "total_risk_comparison": data.get("total_risk_comparison", ""),
            "certainty_appeal": data.get("certainty_appeal", ""),
            "opportunity_cost": data.get("opportunity_cost", ""),
            "emotional_vs_rational": data.get("emotional_vs_rational", ""),
            "pseudocertainty": data.get("pseudocertainty", False),
            "catastrophic_risk": data.get("catastrophic_risk", False),
            "cost_effectiveness": data.get("cost_effectiveness", ""),
            "recommendation": data.get("recommendation", ""),
        }

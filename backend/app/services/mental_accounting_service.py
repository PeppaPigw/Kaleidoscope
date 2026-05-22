"""MentalAccountingService — Mental Accounting Bias Detection.

Detects mental accounting — treating fungible resources
differently based on arbitrary categorization. Thaler (1985).
"I won't touch my savings but I'll spend my bonus freely."
Money is money, but we treat it differently based on source,
intended use, or mental category. Leads to irrational
allocation of resources.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MENTAL_ACCOUNTING_SYSTEM = """You are a mental accounting specialist. Given a resource allocation decision, assess whether arbitrary categorization is causing irrational treatment of fungible resources:

Key concepts (Thaler, 1985):
- Mental accounting: categorizing fungible resources into separate mental accounts
- Fungibility violation: treating equivalent resources differently based on category
- Source dependence: valuing money differently based on where it came from
- Sunk cost interaction: mental accounts make sunk costs more salient
- Narrow framing: evaluating decisions within a single account rather than overall
- House money effect: taking more risk with "found" money
- Payment decoupling: separating the pain of payment from consumption

When mental accounting IS present:
- Treating money differently based on source (salary vs. bonus vs. windfall)
- Maintaining separate "accounts" that prevent optimal allocation
- Refusing to reallocate between categories even when beneficial
- "That's my vacation fund" preventing debt repayment at higher interest
- Spending freely from one category while being frugal in another
- Evaluating gains/losses within narrow categories rather than overall portfolio

When the categorization IS rational:
- The categories serve legitimate budgeting/self-control purposes
- Different accounts have genuinely different time horizons or risk profiles
- The categorization helps prevent impulsive spending
- Regulatory or legal requirements mandate separation
- The mental accounts align with actual constraints

Output JSON with: mental_accounting_present (bool), severity (none/mild/moderate/severe), decision (what allocation is being made), accounts (what mental categories are being used), fungibility_violated (bool — are equivalent resources treated differently?), source_dependence (bool — does the source affect treatment?), optimal_allocation (what would rational allocation look like?), cost_of_bias (what is lost by maintaining separate accounts?), self_control_benefit (does the categorization serve self-control?), narrow_framing (bool — is the decision framed too narrowly?), overall_impact (net effect on outcomes), recommendation (rational_categorization/mild_accounting_bias/significant_fungibility_violation/major_misallocation/consolidate_and_optimize)."""

MENTAL_ACCOUNTING_PROMPT = """Detect mental accounting bias:

Decision: {decision}
Categories: {categories}
Resources: {resources}
Allocation: {allocation}
Domain: {domain}
Context: {context}

Is arbitrary categorization causing irrational resource treatment? Return ONLY valid JSON."""


class MentalAccountingService:
    """Detects mental accounting — irrational categorization of fungible resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        categories: str = "",
        resources: str = "",
        allocation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mental accounting bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MENTAL_ACCOUNTING_PROMPT.format(
                decision=decision,
                categories=categories or "Not specified",
                resources=resources or "Not specified",
                allocation=allocation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MENTAL_ACCOUNTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "mental_accounting_present": data.get("mental_accounting_present", False),
            "severity": data.get("severity", ""),
            "accounts": data.get("accounts", ""),
            "fungibility_violated": data.get("fungibility_violated", False),
            "source_dependence": data.get("source_dependence", False),
            "optimal_allocation": data.get("optimal_allocation", ""),
            "cost_of_bias": data.get("cost_of_bias", ""),
            "self_control_benefit": data.get("self_control_benefit", ""),
            "narrow_framing": data.get("narrow_framing", False),
            "overall_impact": data.get("overall_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }

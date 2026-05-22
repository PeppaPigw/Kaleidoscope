"""IsolatedDemandRigorService — Isolated Demand for Rigor Detection.

Detects isolated demand for rigor — applying strict evidential standards
selectively to claims one disagrees with while accepting equally or less
supported claims that align with one's existing beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ISOLATED_DEMAND_RIGOR_SYSTEM = """You are an isolated demand for rigor specialist. Given an evidential standard being applied, assess whether rigor is being demanded selectively:

Key concepts:
- Isolated demand for rigor: strict standards applied only to opposing views
- Selective skepticism: doubting only what you disagree with
- Asymmetric evidence standards: different bars for different conclusions
- Motivated reasoning: rigor as a weapon rather than a principle
- Consistent epistemology: applying the same standards to all claims
- Double standard: accepting weak evidence for preferred conclusions
- Principle of charity: applying standards fairly across positions

When isolated demand IS present:
- Strict evidence demanded for claims the person disagrees with
- Weaker evidence accepted for claims the person agrees with
- "Show me the peer-reviewed study" for one side but not the other
- Standards shift depending on which conclusion is supported
- Rigor used as a rhetorical weapon rather than genuine epistemology
- The person would not apply the same standard to their own beliefs
- Skepticism is directional rather than principled

When rigorous standards ARE consistently applied:
- The same evidential bar is applied regardless of conclusion
- The person acknowledges when their own beliefs lack strong evidence
- Standards are stated in advance, not post-hoc
- Rigor is applied to all claims in the domain equally
- The person can articulate their general epistemological standards
- Skepticism is principled and non-directional
- The demand for evidence is proportional to the claim's importance

Output JSON with: isolated_demand_present (bool), severity (none/mild/moderate/severe), claim_challenged (what claim faces the demand), standard_applied (what standard is demanded), comparison_claims (what claims escape the same standard), asymmetry (how standards differ), consistency (are standards applied consistently), recommendation (standards_consistent/mild_selectivity/significant_isolated_demand/major_epistemic_double_standard/apply_standards_consistently)."""

ISOLATED_DEMAND_RIGOR_PROMPT = """Detect isolated demand for rigor:

Claim challenged: {claim}
Standard applied: {standard}
Comparison: {comparison}
Consistency: {consistency}
Domain: {domain}
Context: {context}

Is rigor being demanded selectively — strict standards for disagreed-with claims but not others? Return ONLY valid JSON."""


class IsolatedDemandRigorService:
    """Detects isolated demand for rigor — selective application of evidential standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        standard: str = "",
        comparison: str = "",
        consistency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect isolated demand for rigor."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ISOLATED_DEMAND_RIGOR_PROMPT.format(
                claim=claim,
                standard=standard or "Not specified",
                comparison=comparison or "Not specified",
                consistency=consistency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ISOLATED_DEMAND_RIGOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "isolated_demand_present": data.get("isolated_demand_present", False),
            "severity": data.get("severity", ""),
            "standard_applied": data.get("standard_applied", ""),
            "comparison_claims": data.get("comparison_claims", ""),
            "asymmetry": data.get("asymmetry", ""),
            "consistency": data.get("consistency", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""IsolatedDemandForRigorService — Isolated Demand for Rigor Detection.

Detects isolated demand for rigor — applying strict evidential
standards selectively to opposing views while accepting one's own
views on weaker evidence. A form of motivated skepticism where
the bar for evidence is raised only for conclusions one doesn't
want to accept. "Show me the peer-reviewed study" for claims you
dislike, "it's obvious" for claims you favor.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ISOLATED_DEMAND_SYSTEM = """You are an isolated demand for rigor specialist. Given an evidential dispute, assess whether rigorous standards are being applied selectively:

Key concepts:
- Isolated demand for rigor: strict standards only for opposing views
- Motivated skepticism: skepticism proportional to disagreement
- Asymmetric evidence standards: different bars for different conclusions
- Selective scrutiny: examining opposing evidence more carefully
- Burden of proof shifting: demanding proof only from the other side
- Hyperskepticism: unreasonable doubt applied selectively
- Double standard: accepting weak evidence for preferred conclusions

When isolated demand for rigor IS present:
- Demanding peer-reviewed studies for opposing claims but not own claims
- Accepting anecdotes for preferred views, demanding data for opposing views
- "Correlation isn't causation" only for inconvenient correlations
- Scrutinizing methodology only of studies with unwanted conclusions
- "That's just one study" for opposing evidence, "studies show" for own
- Moving goalposts when opposing evidence meets stated standards
- Different epistemological standards for different conclusions

When rigorous standards ARE appropriate:
- The same standards are applied consistently to all claims
- Higher standards for higher-stakes claims (proportional skepticism)
- Methodological criticism is specific and applies regardless of conclusion
- The person acknowledges when their own views lack strong evidence
- Standards are stated in advance, not after seeing results

Output JSON with: isolated_demand_present (bool), severity (none/mild/moderate/severe), claim_scrutinized (what claim faces high standards), claim_accepted (what claim is accepted on weaker evidence), standard_for_opposing (what evidence is demanded), standard_for_own (what evidence is accepted), consistency (are standards applied consistently), motivation (what motivates the asymmetry), recommendation (standards_consistent/mild_selective_scrutiny/significant_isolated_demand/major_asymmetric_skepticism/apply_standards_consistently)."""

ISOLATED_DEMAND_PROMPT = """Detect isolated demand for rigor:

Dispute: {dispute}
Standard applied: {standard}
Own evidence: {own_evidence}
Opposing evidence: {opposing_evidence}
Domain: {domain}
Context: {context}

Are rigorous evidential standards being applied selectively to opposing views? Return ONLY valid JSON."""


class IsolatedDemandForRigorService:
    """Detects isolated demand for rigor — selective application of evidential standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dispute: str,
        *,
        standard: str = "",
        own_evidence: str = "",
        opposing_evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect isolated demand for rigor."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ISOLATED_DEMAND_PROMPT.format(
                dispute=dispute,
                standard=standard or "Not specified",
                own_evidence=own_evidence or "Not specified",
                opposing_evidence=opposing_evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ISOLATED_DEMAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dispute": dispute[:200],
            "isolated_demand_present": data.get("isolated_demand_present", False),
            "severity": data.get("severity", ""),
            "claim_scrutinized": data.get("claim_scrutinized", ""),
            "claim_accepted": data.get("claim_accepted", ""),
            "standard_for_opposing": data.get("standard_for_opposing", ""),
            "standard_for_own": data.get("standard_for_own", ""),
            "consistency": data.get("consistency", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }

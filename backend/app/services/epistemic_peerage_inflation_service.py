"""EpistemicPeerageInflationService — Epistemic Peerage Inflation Detection.

Detects epistemic peerage inflation — treating non-peers as peers
or peers as non-peers to manage disagreement, manipulating who
counts as an epistemic peer based on convenience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PEERAGE_INFLATION_SYSTEM = """You are an epistemic peerage inflation specialist. Given a credibility assessment, evaluate whether peer status is being manipulated:

Key concepts:
- Epistemic peerage inflation: manipulating who counts as peer
- Peer demotion: demoting disagreeing experts to non-peer status
- Peer promotion: promoting agreeing non-experts to peer status
- Motivated peerage: peer status determined by agreement
- Credential gerrymandering: redefining qualifications to include/exclude
- Moving the goalposts on expertise: changing criteria for peerage
- Convenience peerage: peer status serving argumentative purposes

When epistemic peerage inflation IS present:
- Peer status assigned based on agreement, not qualifications
- Disagreeing experts demoted from peer status
- Agreeing non-experts promoted to peer status
- Qualifications for peerage change based on position
- Credential requirements shift to include/exclude conveniently
- Expertise criteria manipulated for argumentative purposes
- Peer assessment motivated by desired conclusion

When peerage assessment is appropriate:
- Peer status based on relevant qualifications
- Consistent criteria applied regardless of position
- Expertise assessed independently of agreement
- Qualifications defined before knowing positions
- Peer status stable across disagreements
- Criteria for expertise transparent and consistent
- Assessment based on track record and training

Output JSON with: inflation_present (bool), severity (none/mild/moderate/severe), assessment (what peerage assessment is made), manipulation (how peer status is manipulated), criteria_shift (how criteria change), motivation (what motivates the manipulation), recommendation (appropriate_peerage_assessment/mild_criteria_flexibility/significant_peerage_inflation/major_credential_gerrymandering/apply_consistent_criteria)."""

EPISTEMIC_PEERAGE_INFLATION_PROMPT = """Detect epistemic peerage inflation:

Assessment: {assessment}
Criteria used: {criteria}
Who is included: {included}
Who is excluded: {excluded}
Domain: {domain}
Context: {context}

Is peer status being manipulated based on agreement rather than qualifications? Return ONLY valid JSON."""


class EpistemicPeerageInflationService:
    """Detects epistemic peerage inflation — manipulating who counts as a peer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        criteria: str = "",
        included: str = "",
        excluded: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic peerage inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PEERAGE_INFLATION_PROMPT.format(
                assessment=assessment,
                criteria=criteria or "Not specified",
                included=included or "Not specified",
                excluded=excluded or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PEERAGE_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "inflation_present": data.get("inflation_present", False),
            "severity": data.get("severity", ""),
            "manipulation": data.get("manipulation", ""),
            "criteria_shift": data.get("criteria_shift", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }

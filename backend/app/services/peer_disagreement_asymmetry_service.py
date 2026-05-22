"""PeerDisagreementAsymmetryService — Peer Disagreement Asymmetry Detection.

Detects peer disagreement asymmetry — treating disagreement with
epistemic peers differently depending on whether they agree or
disagree with you, selectively applying peer principles.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PEER_DISAGREEMENT_ASYMMETRY_SYSTEM = """You are a peer disagreement asymmetry specialist. Given a response to disagreement, assess whether peer disagreement is being handled asymmetrically:

Key concepts:
- Peer disagreement asymmetry: different treatment of agreeing vs. disagreeing peers
- Selective steadfastness: holding firm only against disagreeing peers
- Selective conciliation: only updating toward agreeing peers
- Epistemic self-trust: trusting own judgment over equally qualified peers
- Symmetry principle: treating peer disagreement consistently
- Motivated peer assessment: judging peerage based on agreement
- Double standard: different epistemic standards for allies vs. opponents

When peer disagreement asymmetry IS present:
- Disagreeing peers dismissed while agreeing peers cited
- Different standards applied to agreeing vs. disagreeing peers
- Peer status questioned only when they disagree
- Steadfastness toward disagreement but conciliation toward agreement
- Motivated assessment of who counts as a peer
- Agreement treated as evidence of competence
- Disagreement treated as evidence of incompetence

When peer disagreement handling is appropriate:
- Consistent standards applied regardless of agreement
- Peer status assessed independently of position
- Both agreement and disagreement given appropriate weight
- Symmetry principle respected
- Reasons for disagreement evaluated on merits
- Own position updated consistently
- Peer assessment based on relevant criteria

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), disagreement (what is disagreed about), treatment_of_agreeing (how agreeing peers are treated), treatment_of_disagreeing (how disagreeing peers are treated), double_standard (what double standard exists), recommendation (appropriate_peer_handling/mild_asymmetry/significant_peer_disagreement_asymmetry/major_double_standard/apply_consistent_standards)."""

PEER_DISAGREEMENT_ASYMMETRY_PROMPT = """Detect peer disagreement asymmetry:

Response: {response}
Agreeing peers: {agreeing}
Disagreeing peers: {disagreeing}
Standards applied: {standards}
Domain: {domain}
Context: {context}

Is disagreement with peers being handled asymmetrically based on whether they agree or disagree? Return ONLY valid JSON."""


class PeerDisagreementAsymmetryService:
    """Detects peer disagreement asymmetry — inconsistent treatment of peer disagreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        response: str,
        *,
        agreeing: str = "",
        disagreeing: str = "",
        standards: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect peer disagreement asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PEER_DISAGREEMENT_ASYMMETRY_PROMPT.format(
                response=response,
                agreeing=agreeing or "Not specified",
                disagreeing=disagreeing or "Not specified",
                standards=standards or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PEER_DISAGREEMENT_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "response": response[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "treatment_of_agreeing": data.get("treatment_of_agreeing", ""),
            "treatment_of_disagreeing": data.get("treatment_of_disagreeing", ""),
            "double_standard": data.get("double_standard", ""),
            "recommendation": data.get("recommendation", ""),
        }

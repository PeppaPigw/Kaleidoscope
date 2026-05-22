"""FalseConsensusAsymmetryService — False Consensus Effect (Asymmetric) Detection.

Detects the false consensus effect in its asymmetric form —
overestimating how much others agree with you, especially on
controversial positions, while underestimating agreement on
positions you oppose.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_CONSENSUS_ASYMMETRY_SYSTEM = """You are a false consensus asymmetry specialist. Given a belief or claim about consensus, assess whether agreement is being overestimated:

Key concepts:
- False consensus effect: overestimating others' agreement
- Projection of beliefs: assuming others think like you
- Consensus overestimation: believing your view is majority
- Echo chamber effect: limited exposure inflating perceived consensus
- Asymmetric consensus: overestimating agreement with own views
- Social proof fabrication: claiming consensus that doesn't exist
- Majority illusion: network effects creating false sense of majority

When false consensus asymmetry IS present:
- Agreement with own position overestimated
- Disagreement with own position underestimated
- Limited sample treated as representative
- Echo chamber mistaken for broad consensus
- Own view assumed to be default or majority
- Dissent minimized or treated as fringe
- Consensus claimed without evidence

When consensus assessment is appropriate:
- Actual polling or survey data cited
- Sample representativeness considered
- Dissent acknowledged and quantified
- Uncertainty about consensus stated
- Own position not assumed to be majority
- Evidence for consensus level provided
- Limitations of consensus knowledge noted

Output JSON with: false_consensus_present (bool), severity (none/mild/moderate/severe), claim (what consensus is claimed), actual_evidence (what evidence exists for consensus), overestimation (how agreement is overestimated), echo_chamber (what limited sample is used), recommendation (appropriate_consensus_claim/mild_overestimation/significant_false_consensus/major_consensus_fabrication/verify_actual_consensus)."""

FALSE_CONSENSUS_ASYMMETRY_PROMPT = """Detect false consensus asymmetry:

Claim: {claim}
Consensus claimed: {consensus}
Evidence for consensus: {evidence}
Dissent acknowledged: {dissent}
Domain: {domain}
Context: {context}

Is agreement being overestimated or consensus being claimed without adequate evidence? Return ONLY valid JSON."""


class FalseConsensusAsymmetryService:
    """Detects false consensus asymmetry — overestimating agreement with own views."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        consensus: str = "",
        evidence: str = "",
        dissent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false consensus asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_CONSENSUS_ASYMMETRY_PROMPT.format(
                claim=claim,
                consensus=consensus or "Not specified",
                evidence=evidence or "Not specified",
                dissent=dissent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_CONSENSUS_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "false_consensus_present": data.get("false_consensus_present", False),
            "severity": data.get("severity", ""),
            "actual_evidence": data.get("actual_evidence", ""),
            "overestimation": data.get("overestimation", ""),
            "echo_chamber": data.get("echo_chamber", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicConsensusFragilityDeeperService — Epistemic Consensus Fragility Detection (Deeper).

Detects epistemic consensus fragility — consensus that appears solid
but is actually fragile and could collapse with new evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONSENSUS_FRAGILITY_DEEPER_SYSTEM = """You are an epistemic consensus fragility specialist. Given apparently solid but actually fragile consensus, assess fragility:

Key concepts:
- Epistemic consensus fragility: consensus appearing solid but actually fragile
- Thin evidence base: consensus resting on thin evidence
- Key assumption vulnerability: consensus depending on few key assumptions
- Replication crisis: consensus based on unreplicated findings
- Preference cascade potential: potential for rapid consensus collapse
- Hidden disagreement: disagreement hidden beneath surface consensus
- Single point of failure: consensus depending on single study or authority

When epistemic consensus fragility IS present:
- Consensus appears solid but fragile
- Evidence base thin
- Key assumptions vulnerable
- Findings unreplicated
- Preference cascade possible
- Disagreement hidden
- Single points of failure

When no consensus fragility:
- Consensus genuinely robust
- Evidence base thick
- Assumptions well-supported
- Findings replicated
- Consensus stable
- Agreement genuine
- Multiple supports

Output JSON with: consensus_fragility_detected (bool), severity (none/mild/moderate/severe), thin_evidence_base (what evidence thin), key_assumption_vulnerability (what assumptions vulnerable), hidden_disagreement (what disagreement hidden), single_point_failure (what single points), recommendation (no_consensus_fragility/mild_robustness_testing/significant_evidence_strengthening/major_intensive_consensus_rebuilding/emergency_complete_consensus_fragility)."""

EPISTEMIC_CONSENSUS_FRAGILITY_DEEPER_PROMPT = """Detect epistemic consensus fragility:

Thin evidence base: {thin_evidence_base}
Key assumption vulnerability: {key_assumption_vulnerability}
Hidden disagreement: {hidden_disagreement}
Single point of failure: {single_point_failure}
Domain: {domain}
Context: {context}

Does consensus appear solid but is actually fragile? Return ONLY valid JSON."""


class EpistemicConsensusFragilityDeeperService:
    """Detects epistemic consensus fragility — solid-seeming but fragile."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thin_evidence_base: str,
        *,
        key_assumption_vulnerability: str = "",
        hidden_disagreement: str = "",
        single_point_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic consensus fragility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONSENSUS_FRAGILITY_DEEPER_PROMPT.format(
                thin_evidence_base=thin_evidence_base,
                key_assumption_vulnerability=key_assumption_vulnerability or "Not specified",
                hidden_disagreement=hidden_disagreement or "Not specified",
                single_point_failure=single_point_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONSENSUS_FRAGILITY_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thin_evidence_base": thin_evidence_base[:200],
            "consensus_fragility_detected": data.get("consensus_fragility_detected", False),
            "severity": data.get("severity", ""),
            "key_assumption_vulnerability": data.get("key_assumption_vulnerability", ""),
            "hidden_disagreement": data.get("hidden_disagreement", ""),
            "single_point_failure": data.get("single_point_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }

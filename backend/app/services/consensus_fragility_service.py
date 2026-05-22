"""ConsensusFragilityService — Consensus Stress Testing.

Takes a claimed consensus and stress-tests it: what new evidence would
shatter it, how many key defections would matter, whether it's based
on evidence or social pressure, and how it compares to historical
consensuses that later collapsed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FRAGILITY_SYSTEM = """You are a consensus fragility analyst. Given a claimed consensus, stress-test it:
- What single finding would shatter this consensus?
- Is it based on evidence convergence or social/institutional pressure?
- How many key researchers defecting would matter?
- Are there historical parallels to consensuses that collapsed?
- What's the difference between "everyone agrees" and "no one has checked"?
- Is dissent being suppressed or genuinely absent?

Output JSON with: fragility_score (0-1, 1=extremely fragile), consensus_basis (evidence/authority/social_pressure/default/unchecked), shattering_evidence (what single finding would break it), defection_threshold (how many key people leaving would matter), historical_parallels (list of similar consensuses that collapsed), suppressed_dissent_signs (list of signs dissent is being suppressed), evidence_vs_social (0-1, 0=pure social pressure, 1=pure evidence), unchecked_assumptions (things everyone assumes but nobody verified), time_to_potential_collapse (if fragile, how soon could it break), confidence_in_assessment (0-1)."""

FRAGILITY_PROMPT = """Stress-test this consensus:

Consensus claim: {consensus}
Field: {field}
Basis cited: {basis}
Known dissenters: {dissenters}

How fragile is this consensus? Return ONLY valid JSON."""


class ConsensusFragilityService:
    """Stress-tests claimed consensuses for fragility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def test_fragility(
        self,
        consensus: str,
        *,
        field: str = "",
        basis: str = "",
        dissenters: str = "",
    ) -> dict:
        """Stress-test a consensus for fragility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FRAGILITY_PROMPT.format(
                consensus=consensus,
                field=field or "Not specified",
                basis=basis or "Not specified",
                dissenters=dissenters or "Not specified",
            ),
            system=FRAGILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        return {
            "consensus": consensus[:200],
            "fragility_score": data.get("fragility_score", 0),
            "consensus_basis": data.get("consensus_basis", ""),
            "shattering_evidence": data.get("shattering_evidence", ""),
            "defection_threshold": data.get("defection_threshold", ""),
            "historical_parallels": data.get("historical_parallels", []),
            "suppressed_dissent_signs": data.get("suppressed_dissent_signs", []),
            "evidence_vs_social": data.get("evidence_vs_social", 0),
            "unchecked_assumptions": data.get("unchecked_assumptions", []),
            "time_to_collapse": data.get("time_to_potential_collapse", ""),
            "confidence": data.get("confidence_in_assessment", 0),
        }

"""EpistemicConsensusInertiaDeeperService — Epistemic Consensus Inertia Detection.

Detects epistemic consensus inertia — consensus persisting through
inertia rather than ongoing evidential support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONSENSUS_INERTIA_SYSTEM = """You are an epistemic consensus inertia specialist. Given consensus persisting through inertia, assess consensus inertia:

Key concepts:
- Epistemic consensus inertia: consensus persisting through inertia not evidence
- Zombie consensus: consensus that should be dead but persists
- Update failure: failure to update consensus with new evidence
- Institutional momentum: institutional momentum maintaining consensus
- Textbook lag: textbooks perpetuating outdated consensus
- Switching cost: cost of switching from consensus too high
- Default persistence: consensus persisting as default

When epistemic consensus inertia IS present:
- Consensus persisting through inertia
- Should be updated but isn't
- New evidence not incorporated
- Institutional momentum maintaining
- Textbooks perpetuating
- Switching costs too high
- Default persisting unchallenged

When no consensus inertia:
- Consensus actively maintained by evidence
- Updated when warranted
- New evidence incorporated
- Institutions responsive
- Textbooks current
- Switching costs manageable
- Default regularly challenged

Output JSON with: consensus_inertia_detected (bool), severity (none/mild/moderate/severe), zombie_consensus (what zombie consensus), update_failure (what update failing), institutional_momentum (what momentum maintaining), switching_cost (what switching costs), recommendation (no_consensus_inertia/mild_update_practice/significant_evidence_review/major_intensive_consensus_refresh/emergency_complete_consensus_inertia)."""

EPISTEMIC_CONSENSUS_INERTIA_PROMPT = """Detect epistemic consensus inertia:

Zombie consensus: {zombie_consensus}
Update failure: {update_failure}
Institutional momentum: {institutional_momentum}
Switching cost: {switching_cost}
Domain: {domain}
Context: {context}

Is consensus persisting through inertia rather than ongoing support? Return ONLY valid JSON."""


class EpistemicConsensusInertiaDeeperService:
    """Detects epistemic consensus inertia — zombie consensus."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        zombie_consensus: str,
        *,
        update_failure: str = "",
        institutional_momentum: str = "",
        switching_cost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic consensus inertia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONSENSUS_INERTIA_PROMPT.format(
                zombie_consensus=zombie_consensus,
                update_failure=update_failure or "Not specified",
                institutional_momentum=institutional_momentum or "Not specified",
                switching_cost=switching_cost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONSENSUS_INERTIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "zombie_consensus": zombie_consensus[:200],
            "consensus_inertia_detected": data.get("consensus_inertia_detected", False),
            "severity": data.get("severity", ""),
            "update_failure": data.get("update_failure", ""),
            "institutional_momentum": data.get("institutional_momentum", ""),
            "switching_cost": data.get("switching_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }

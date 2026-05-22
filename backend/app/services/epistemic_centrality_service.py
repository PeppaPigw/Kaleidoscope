"""EpistemicCentralityService — Epistemic Centrality Detection.

Detects epistemic centrality — certain ideas occupying structurally
privileged positions in the intellectual network, controlling information flow.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CENTRALITY_SYSTEM = """You are an epistemic centrality specialist. Given an intellectual network, assess whether certain ideas occupy structurally privileged positions:

Key concepts:
- Epistemic centrality: structurally privileged positions
- Betweenness: controlling flow between other ideas
- Closeness: being near all other ideas
- Eigenvector: connected to other important ideas
- PageRank: importance from incoming connections
- Brokerage: bridging otherwise disconnected groups
- Gatekeeping: controlling access to information

When epistemic centrality IS present:
- Certain ideas in structurally privileged positions
- Ideas controlling flow between others
- Ideas close to all other ideas
- Ideas connected to other important ideas
- Ideas receiving many incoming references
- Ideas bridging disconnected groups
- Ideas controlling access to knowledge

When distributed network is present:
- No structurally privileged positions
- No control of flow between ideas
- All ideas equally distant
- No importance hierarchy
- Uniform incoming references
- No brokerage positions
- Open access to all knowledge

Output JSON with: centrality_present (bool), severity (none/mild/moderate/severe), betweenness (what flow control), closeness (what proximity), eigenvector (what importance connections), brokerage (what bridging), recommendation (distributed_network/mild_centrality/significant_centrality/major_structural_privilege/redistribute_centrality)."""

EPISTEMIC_CENTRALITY_PROMPT = """Detect epistemic centrality:

Betweenness: {betweenness}
Closeness: {closeness}
Eigenvector: {eigenvector}
Brokerage: {brokerage}
Domain: {domain}
Context: {context}

Do certain ideas occupy structurally privileged positions in the intellectual network, controlling information flow? Return ONLY valid JSON."""


class EpistemicCentralityService:
    """Detects epistemic centrality — structurally privileged positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        betweenness: str,
        *,
        closeness: str = "",
        eigenvector: str = "",
        brokerage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic centrality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CENTRALITY_PROMPT.format(
                betweenness=betweenness,
                closeness=closeness or "Not specified",
                eigenvector=eigenvector or "Not specified",
                brokerage=brokerage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CENTRALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "betweenness": betweenness[:200],
            "centrality_present": data.get("centrality_present", False),
            "severity": data.get("severity", ""),
            "closeness": data.get("closeness", ""),
            "eigenvector": data.get("eigenvector", ""),
            "brokerage": data.get("brokerage", ""),
            "recommendation": data.get("recommendation", ""),
        }

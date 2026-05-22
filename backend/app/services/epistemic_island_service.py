"""EpistemicIslandService — Epistemic Island Detection.

Detects epistemic islands — isolated belief clusters that are
disconnected from the rest of one's knowledge network.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ISLAND_SYSTEM = """You are an epistemic island specialist. Given a belief system, assess whether isolated belief clusters exist disconnected from broader knowledge:

Key concepts:
- Epistemic island: isolated belief cluster disconnected from knowledge
- Belief isolation: beliefs held without connection to evidence network
- Knowledge fragmentation: knowledge broken into disconnected pieces
- Integration failure: failure to integrate beliefs with broader knowledge
- Compartmentalization: keeping beliefs separate to avoid conflict
- Disconnected conviction: strong conviction without evidential connection
- Orphan beliefs: beliefs without supporting network

When epistemic islands ARE present:
- Belief clusters isolated from broader knowledge
- Beliefs held without connection to evidence network
- Knowledge fragmented into disconnected pieces
- Integration with broader knowledge absent
- Compartmentalization preventing coherence
- Strong conviction without evidential support network
- Beliefs orphaned from justification structure

When integrated knowledge is present:
- Beliefs connected to broader knowledge network
- Evidence network supporting belief clusters
- Knowledge integrated and coherent
- Beliefs connected to justification structure
- Coherence maintained across domains
- Conviction supported by evidential connections

Output JSON with: island_present (bool), severity (none/mild/moderate/severe), belief_cluster (what beliefs are isolated), disconnection (how they are disconnected), broader_knowledge (what broader knowledge exists), integration_failure (why integration fails), recommendation (integrated_knowledge/mild_fragmentation/significant_epistemic_island/major_belief_isolation/integrate_knowledge_network)."""

EPISTEMIC_ISLAND_PROMPT = """Detect epistemic islands:

Belief cluster: {cluster}
Disconnection: {disconnection}
Broader knowledge: {broader}
Integration attempt: {integration}
Domain: {domain}
Context: {context}

Are isolated belief clusters disconnected from broader knowledge? Return ONLY valid JSON."""


class EpistemicIslandService:
    """Detects epistemic islands — isolated belief clusters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cluster: str,
        *,
        disconnection: str = "",
        broader: str = "",
        integration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic islands."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ISLAND_PROMPT.format(
                cluster=cluster,
                disconnection=disconnection or "Not specified",
                broader=broader or "Not specified",
                integration=integration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ISLAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cluster": cluster[:200],
            "island_present": data.get("island_present", False),
            "severity": data.get("severity", ""),
            "disconnection": data.get("disconnection", ""),
            "broader_knowledge": data.get("broader_knowledge", ""),
            "integration_failure": data.get("integration_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }

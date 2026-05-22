"""EpistemicModularityService — Epistemic Modularity Detection.

Detects epistemic modularity — intellectual networks partitioning into
densely connected communities with sparse connections between them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MODULARITY_SYSTEM = """You are an epistemic modularity specialist. Given an intellectual network, assess whether it partitions into dense communities:

Key concepts:
- Epistemic modularity: partitioning into dense communities
- Community: densely connected subgroup
- Modularity score: quality of partition
- Bridge: connection between communities
- Overlap: ideas belonging to multiple communities
- Resolution: scale at which communities are detected
- Hierarchy: communities within communities

When epistemic modularity IS present:
- Network partitioning into dense communities
- Subgroups with many internal connections
- High quality of community partition
- Sparse connections between communities
- Some ideas belonging to multiple groups
- Communities detectable at multiple scales
- Nested community structure

When homogeneous network is present:
- No clear community structure
- Uniform connection density throughout
- Low modularity score
- No sparse boundaries
- No multi-membership
- Same structure at all scales
- No hierarchical nesting

Output JSON with: modularity_present (bool), severity (none/mild/moderate/severe), communities (what subgroups), bridges (what inter-community links), overlap (what multi-membership), hierarchy (what nesting), recommendation (homogeneous_network/mild_modularity/significant_modularity/major_community_structure/bridge_communities)."""

EPISTEMIC_MODULARITY_PROMPT = """Detect epistemic modularity:

Communities: {communities}
Bridges: {bridges}
Overlap: {overlap}
Hierarchy: {hierarchy}
Domain: {domain}
Context: {context}

Does the intellectual network partition into densely connected communities with sparse connections between them? Return ONLY valid JSON."""


class EpistemicModularityService:
    """Detects epistemic modularity — partitioning into dense communities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communities: str,
        *,
        bridges: str = "",
        overlap: str = "",
        hierarchy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic modularity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MODULARITY_PROMPT.format(
                communities=communities,
                bridges=bridges or "Not specified",
                overlap=overlap or "Not specified",
                hierarchy=hierarchy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MODULARITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communities": communities[:200],
            "modularity_present": data.get("modularity_present", False),
            "severity": data.get("severity", ""),
            "bridges": data.get("bridges", ""),
            "overlap": data.get("overlap", ""),
            "hierarchy": data.get("hierarchy", ""),
            "recommendation": data.get("recommendation", ""),
        }

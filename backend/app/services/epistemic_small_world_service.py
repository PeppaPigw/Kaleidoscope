"""EpistemicSmallWorldService — Epistemic Small World Detection.

Detects epistemic small world — intellectual networks where most ideas
are reachable from any other in a small number of steps despite large size.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SMALL_WORLD_SYSTEM = """You are an epistemic small world specialist. Given an intellectual network, assess whether short paths connect most ideas:

Key concepts:
- Epistemic small world: short paths between most ideas
- Six degrees: few hops between any two ideas
- Clustering: local neighborhoods densely connected
- Hub: highly connected central idea
- Weak tie: bridge between distant clusters
- Diameter: longest shortest path
- Average path length: typical distance between ideas

When epistemic small world IS present:
- Most ideas reachable in few steps
- High local clustering of related ideas
- Highly connected hub ideas
- Weak ties bridging distant clusters
- Small network diameter despite large size
- Short average path between any two ideas
- Combination of clustering and short paths

When disconnected network is present:
- Many ideas unreachable from others
- Low clustering of ideas
- No hub ideas connecting clusters
- No bridges between groups
- Large or infinite diameter
- Long average paths
- Neither clustered nor short-pathed

Output JSON with: small_world_present (bool), severity (none/mild/moderate/severe), clustering (what local density), hubs (what central ideas), weak_ties (what bridges), diameter (what longest path), recommendation (disconnected_network/mild_small_world/significant_small_world/major_short_paths/leverage_weak_ties)."""

EPISTEMIC_SMALL_WORLD_PROMPT = """Detect epistemic small world:

Clustering: {clustering}
Hubs: {hubs}
Weak ties: {weak_ties}
Diameter: {diameter}
Domain: {domain}
Context: {context}

Are most ideas reachable from any other in a small number of steps despite the network's large size? Return ONLY valid JSON."""


class EpistemicSmallWorldService:
    """Detects epistemic small world — short paths between most ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        clustering: str,
        *,
        hubs: str = "",
        weak_ties: str = "",
        diameter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic small world."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SMALL_WORLD_PROMPT.format(
                clustering=clustering,
                hubs=hubs or "Not specified",
                weak_ties=weak_ties or "Not specified",
                diameter=diameter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SMALL_WORLD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "clustering": clustering[:200],
            "small_world_present": data.get("small_world_present", False),
            "severity": data.get("severity", ""),
            "hubs": data.get("hubs", ""),
            "weak_ties": data.get("weak_ties", ""),
            "diameter": data.get("diameter", ""),
            "recommendation": data.get("recommendation", ""),
        }

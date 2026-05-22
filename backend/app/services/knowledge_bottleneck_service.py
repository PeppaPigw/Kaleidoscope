"""KnowledgeBottleneckService — Knowledge Bottleneck Detection.

Detects knowledge bottlenecks — single points of failure in
knowledge flow where all understanding must pass through one narrow channel.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_BOTTLENECK_SYSTEM = """You are a knowledge bottleneck specialist. Given a knowledge flow pattern, assess whether single points of failure exist:

Key concepts:
- Knowledge bottleneck: single point of failure in knowledge flow
- Information chokepoint: narrow channel all information must pass through
- Single source dependency: depending on one source for all knowledge
- Gatekeeper bottleneck: one person/source controlling all access
- Fragile knowledge path: knowledge path that breaks if one link fails
- Concentration risk: too much knowledge concentrated in one place
- Redundancy failure: lack of alternative knowledge paths

When knowledge bottleneck IS present:
- Single point of failure in knowledge flow
- All information passing through one narrow channel
- Dependency on single source for critical knowledge
- One gatekeeper controlling all access
- Knowledge path fragile to single failure
- Dangerous concentration of knowledge
- No redundant paths for critical information

When distributed knowledge is present:
- Multiple paths for knowledge flow
- Information accessible through various channels
- Multiple sources for critical knowledge
- Access distributed among multiple parties
- Knowledge paths resilient to individual failures
- Healthy distribution of knowledge
- Redundant paths for critical information

Output JSON with: bottleneck_present (bool), severity (none/mild/moderate/severe), flow (what knowledge flow is affected), chokepoint (where the bottleneck is), dependency (what depends on it), fragility (how fragile the path is), recommendation (distributed_knowledge/mild_concentration/significant_bottleneck/major_single_point_failure/distribute_knowledge_paths)."""

KNOWLEDGE_BOTTLENECK_PROMPT = """Detect knowledge bottleneck:

Knowledge flow: {flow}
Chokepoint: {chokepoint}
Dependency: {dependency}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is there a single point of failure in knowledge flow? Return ONLY valid JSON."""


class KnowledgeBottleneckService:
    """Detects knowledge bottlenecks — single points of failure in knowledge flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow: str,
        *,
        chokepoint: str = "",
        dependency: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge bottleneck."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_BOTTLENECK_PROMPT.format(
                flow=flow,
                chokepoint=chokepoint or "Not specified",
                dependency=dependency or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_BOTTLENECK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow": flow[:200],
            "bottleneck_present": data.get("bottleneck_present", False),
            "severity": data.get("severity", ""),
            "chokepoint": data.get("chokepoint", ""),
            "dependency": data.get("dependency", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }

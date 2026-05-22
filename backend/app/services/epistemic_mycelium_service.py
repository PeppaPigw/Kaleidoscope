"""EpistemicMyceliumService — Epistemic Mycelium Network Detection.

Detects epistemic mycelium — hidden underground networks connecting
ideas that appear separate on the surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MYCELIUM_SYSTEM = """You are an epistemic mycelium specialist. Given an idea network, assess whether hidden underground connections link apparently separate ideas:

Key concepts:
- Epistemic mycelium: hidden networks connecting separate-seeming ideas
- Underground network: connections not visible on the surface
- Nutrient transfer: resources flowing between connected ideas
- Fruiting body: visible manifestations of hidden network
- Wood wide web: vast interconnected knowledge network
- Symbiotic exchange: mutual benefit through hidden connections
- Network resilience: ability to route around damage

When epistemic mycelium IS present:
- Hidden networks connecting ideas that appear separate
- Connections not visible on the surface
- Resources flowing between connected ideas underground
- Visible manifestations emerging from hidden network
- Vast interconnected knowledge network beneath surface
- Mutual benefit flowing through hidden connections
- Network able to route around damage

When isolated ideas are present:
- Ideas genuinely separate with no hidden connections
- No underground networks linking ideas
- No resource flow between ideas
- Each idea standing independently
- No hidden interconnection beneath surface
- No mutual benefit from hidden connections
- Ideas vulnerable to individual damage

Output JSON with: mycelium_present (bool), severity (none/mild/moderate/severe), network (what hidden network exists), connections (what ideas are connected), nutrient_flow (what resources transfer), fruiting (what visible manifestations), recommendation (isolated_ideas/mild_connections/significant_network/major_wood_wide_web/map_and_leverage_network)."""

EPISTEMIC_MYCELIUM_PROMPT = """Detect epistemic mycelium network:

Network: {network}
Connections: {connections}
Nutrient flow: {nutrient_flow}
Fruiting: {fruiting}
Domain: {domain}
Context: {context}

Are hidden underground networks connecting ideas that appear separate on the surface? Return ONLY valid JSON."""


class EpistemicMyceliumService:
    """Detects epistemic mycelium — hidden networks connecting separate ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        network: str,
        *,
        connections: str = "",
        nutrient_flow: str = "",
        fruiting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mycelium network."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MYCELIUM_PROMPT.format(
                network=network,
                connections=connections or "Not specified",
                nutrient_flow=nutrient_flow or "Not specified",
                fruiting=fruiting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MYCELIUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "network": network[:200],
            "mycelium_present": data.get("mycelium_present", False),
            "severity": data.get("severity", ""),
            "connections": data.get("connections", ""),
            "nutrient_flow": data.get("nutrient_flow", ""),
            "fruiting": data.get("fruiting", ""),
            "recommendation": data.get("recommendation", ""),
        }

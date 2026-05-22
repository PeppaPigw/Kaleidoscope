"""EpistemicStratigraphyService — Epistemic Stratigraphy Detection.

Detects epistemic stratigraphy — knowledge layers that reveal
intellectual history through their ordering and composition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRATIGRAPHY_SYSTEM = """You are an epistemic stratigraphy specialist. Given a knowledge layering pattern, assess whether layers reveal intellectual history:

Key concepts:
- Epistemic stratigraphy: knowledge layers revealing intellectual history
- Superposition: newer ideas layered on top of older ones
- Unconformity: gaps in the intellectual record
- Cross-cutting: later ideas cutting across earlier layers
- Index fossil: characteristic ideas that date a layer
- Correlation: matching layers across different knowledge areas
- Disturbance: events that disrupt normal layering

When epistemic stratigraphy IS present:
- Knowledge organized in distinct layers revealing history
- Newer ideas clearly layered on top of older ones
- Gaps in the intellectual record visible between layers
- Later ideas cutting across earlier established layers
- Characteristic ideas that help date intellectual periods
- Layers matching across different knowledge areas
- Events that disrupted normal intellectual layering

When unstructured knowledge is present:
- Knowledge not organized in distinct layers
- No clear temporal ordering of ideas
- No gaps visible in intellectual record
- No cross-cutting relationships
- No characteristic period markers
- No correlation between knowledge areas
- No disruption events visible

Output JSON with: stratigraphy_present (bool), severity (none/mild/moderate/severe), layers (what layers are visible), unconformity (what gaps exist), cross_cutting (what later ideas cut across), index_ideas (what characteristic ideas date layers), recommendation (unstructured_knowledge/mild_layering/significant_stratigraphy/major_historical_record/read_the_layers_for_insight)."""

EPISTEMIC_STRATIGRAPHY_PROMPT = """Detect epistemic stratigraphy:

Layers: {layers}
Unconformity: {unconformity}
Cross cutting: {cross_cutting}
Index ideas: {index_ideas}
Domain: {domain}
Context: {context}

Does knowledge show distinct layers that reveal intellectual history through ordering and composition? Return ONLY valid JSON."""


class EpistemicStratigraphyService:
    """Detects epistemic stratigraphy — knowledge layers revealing intellectual history."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        layers: str,
        *,
        unconformity: str = "",
        cross_cutting: str = "",
        index_ideas: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stratigraphy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRATIGRAPHY_PROMPT.format(
                layers=layers,
                unconformity=unconformity or "Not specified",
                cross_cutting=cross_cutting or "Not specified",
                index_ideas=index_ideas or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRATIGRAPHY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "layers": layers[:200],
            "stratigraphy_present": data.get("stratigraphy_present", False),
            "severity": data.get("severity", ""),
            "unconformity": data.get("unconformity", ""),
            "cross_cutting": data.get("cross_cutting", ""),
            "index_ideas": data.get("index_ideas", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicWeatheringService — Epistemic Weathering Detection.

Detects epistemic weathering — knowledge gradually breaking down
through constant exposure to intellectual elements over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WEATHERING_SYSTEM = """You are an epistemic weathering specialist. Given a knowledge degradation pattern, assess whether constant exposure is gradually breaking down knowledge:

Key concepts:
- Epistemic weathering: knowledge breaking down through constant exposure
- Physical weathering: mechanical breakdown without chemical change
- Chemical weathering: fundamental alteration of knowledge composition
- Biological weathering: living intellectual agents breaking down knowledge
- Freeze-thaw: repeated expansion and contraction cracking knowledge
- Exfoliation: surface layers peeling away from knowledge
- Regolith: broken-down knowledge fragments accumulating

When epistemic weathering IS present:
- Knowledge gradually breaking down through constant exposure
- Mechanical breakdown of knowledge without fundamental change
- Fundamental alteration of knowledge composition over time
- Living intellectual agents actively breaking down knowledge
- Repeated cycles cracking knowledge structures
- Surface layers peeling away from core knowledge
- Broken-down knowledge fragments accumulating

When preserved knowledge is present:
- Knowledge maintained despite environmental exposure
- No mechanical breakdown occurring
- No fundamental alteration of composition
- No agents actively breaking down knowledge
- No cyclical cracking of structures
- Surface layers remaining intact
- Knowledge maintaining its coherent form

Output JSON with: weathering_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge weathers), exposure (what elements cause weathering), type (physical/chemical/biological), fragments (what fragments result), recommendation (preserved_knowledge/mild_weathering/significant_breakdown/major_disintegration/protect_from_exposure)."""

EPISTEMIC_WEATHERING_PROMPT = """Detect epistemic weathering:

Knowledge: {knowledge}
Exposure: {exposure}
Type: {weathering_type}
Fragments: {fragments}
Domain: {domain}
Context: {context}

Is knowledge gradually breaking down through constant exposure to intellectual elements? Return ONLY valid JSON."""


class EpistemicWeatheringService:
    """Detects epistemic weathering — gradual knowledge breakdown through exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        exposure: str = "",
        weathering_type: str = "",
        fragments: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic weathering."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WEATHERING_PROMPT.format(
                knowledge=knowledge,
                exposure=exposure or "Not specified",
                weathering_type=weathering_type or "Not specified",
                fragments=fragments or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WEATHERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "weathering_present": data.get("weathering_present", False),
            "severity": data.get("severity", ""),
            "exposure": data.get("exposure", ""),
            "type": data.get("type", ""),
            "fragments": data.get("fragments", ""),
            "recommendation": data.get("recommendation", ""),
        }

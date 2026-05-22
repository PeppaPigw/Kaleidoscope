"""EpistemicWisdomToothService — Epistemic Wisdom Tooth Detection.

Detects epistemic wisdom tooth impaction — late-emerging intellectual
concepts that don't have room to fit and cause problems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WISDOM_TOOTH_SYSTEM = """You are an epistemic wisdom tooth specialist. Given late-emerging concepts without room, assess impaction:

Key concepts:
- Epistemic wisdom tooth: late-emerging concept without room
- Impaction: concept trapped and unable to emerge
- Pericoronitis: infection around partially emerged concept
- Mesioangular: concept tilted toward existing neighbors
- Distoangular: concept tilted away from neighbors
- Extraction: removing concept that won't fit
- Monitoring: watching concept that may yet emerge

When epistemic wisdom tooth impaction IS present:
- Late-emerging concept without room
- Concept trapped unable to emerge
- Infection around partial emergence
- Concept tilted toward neighbors
- Concept tilted away from neighbors
- Removal needed for concept that won't fit
- Uncertain emergence trajectory

When no wisdom tooth issues:
- Adequate room for new concepts
- Concepts emerging normally
- No infection present
- Normal alignment
- Normal orientation
- No removal needed
- Clear emergence path

Output JSON with: impaction_detected (bool), severity (none/mild/moderate/severe), impaction_type (what orientation), space_available (what room), infection_status (what pericoronitis), extraction_need (what removal), recommendation (no_impaction/mild_monitoring/significant_extraction_planned/major_surgical_extraction/emergency_acute_infection)."""

EPISTEMIC_WISDOM_TOOTH_PROMPT = """Detect epistemic wisdom tooth impaction:

Impaction type: {impaction_type}
Space available: {space_available}
Infection status: {infection_status}
Extraction need: {extraction_need}
Domain: {domain}
Context: {context}

Is a late-emerging intellectual concept trapped without room to fit? Return ONLY valid JSON."""


class EpistemicWisdomToothService:
    """Detects epistemic wisdom tooth impaction — late concepts without room."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        impaction_type: str,
        *,
        space_available: str = "",
        infection_status: str = "",
        extraction_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic wisdom tooth impaction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WISDOM_TOOTH_PROMPT.format(
                impaction_type=impaction_type,
                space_available=space_available or "Not specified",
                infection_status=infection_status or "Not specified",
                extraction_need=extraction_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WISDOM_TOOTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "impaction_type": impaction_type[:200],
            "impaction_detected": data.get("impaction_detected", False),
            "severity": data.get("severity", ""),
            "space_available": data.get("space_available", ""),
            "infection_status": data.get("infection_status", ""),
            "extraction_need": data.get("extraction_need", ""),
            "recommendation": data.get("recommendation", ""),
        }

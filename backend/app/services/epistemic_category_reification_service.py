"""EpistemicCategoryReificationService — Epistemic Category Reification Detection.

Detects epistemic category reification — treating abstract categories
as concrete real things, confusing the map with the territory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATEGORY_REIFICATION_SYSTEM = """You are an epistemic category reification specialist. Given reified categories, assess category reification:

Key concepts:
- Epistemic category reification: treating abstract categories as concrete things
- Map-territory confusion: confusing category (map) with reality (territory)
- Nominal realism: treating names as revealing real essences
- Statistical artifact reification: treating statistical constructs as real entities
- Diagnostic reification: treating diagnostic categories as real diseases
- Score reification: treating scores as measuring real things
- Construct reification: treating theoretical constructs as observable entities

When epistemic category reification IS present:
- Abstract categories treated as concrete
- Map confused with territory
- Names treated as essences
- Statistical artifacts reified
- Diagnoses treated as real entities
- Scores treated as real measurements
- Constructs treated as observable

When no category reification:
- Categories recognized as abstractions
- Map-territory distinguished
- Names recognized as labels
- Statistical constructs understood
- Diagnoses as useful fictions
- Scores as approximations
- Constructs as theoretical tools

Output JSON with: category_reification_detected (bool), severity (none/mild/moderate/severe), map_territory_confusion (what map-territory confused), nominal_realism (what names treated as essences), statistical_reification (what statistics reified), construct_reification (what constructs reified), recommendation (no_category_reification/mild_abstraction_awareness/significant_construct_recognition/major_intensive_reification_correction/emergency_complete_category_reification)."""

EPISTEMIC_CATEGORY_REIFICATION_PROMPT = """Detect epistemic category reification:

Map-territory confusion: {map_territory_confusion}
Nominal realism: {nominal_realism}
Statistical reification: {statistical_reification}
Construct reification: {construct_reification}
Domain: {domain}
Context: {context}

Are abstract categories being treated as concrete real things? Return ONLY valid JSON."""


class EpistemicCategoryReificationService:
    """Detects epistemic category reification — abstract as concrete."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        map_territory_confusion: str,
        *,
        nominal_realism: str = "",
        statistical_reification: str = "",
        construct_reification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic category reification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATEGORY_REIFICATION_PROMPT.format(
                map_territory_confusion=map_territory_confusion,
                nominal_realism=nominal_realism or "Not specified",
                statistical_reification=statistical_reification or "Not specified",
                construct_reification=construct_reification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATEGORY_REIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "map_territory_confusion": map_territory_confusion[:200],
            "category_reification_detected": data.get("category_reification_detected", False),
            "severity": data.get("severity", ""),
            "nominal_realism": data.get("nominal_realism", ""),
            "statistical_reification": data.get("statistical_reification", ""),
            "construct_reification": data.get("construct_reification", ""),
            "recommendation": data.get("recommendation", ""),
        }

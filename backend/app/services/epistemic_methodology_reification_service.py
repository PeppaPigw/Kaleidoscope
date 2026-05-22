"""EpistemicMethodologyReificationService - Epistemic Methodology Reification Detection.

Detects reification treating abstract constructs as concrete entities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METHODOLOGY_REIFICATION_SYSTEM = """You are an epistemic methodology reification specialist. Given construct concretization, assess reification:

Key concepts:
- Epistemic methodology reification: treating abstract constructs as concrete entities
- Construct concretization: making an abstract construct seem like a thing
- Map-territory confusion: confusing representation with reality
- Model as reality: treating the model as the world itself
- Abstraction materialization: treating abstractions as material objects

When reification IS present:
- Constructs are treated as concrete entities
- The map is confused with the territory
- Models are treated as reality
- Abstractions are materialized
- Methodological convenience becomes ontology

When no reification:
- Constructs are recognized as abstractions
- Representations are separated from reality
- Models are treated as tools
- Abstractions remain provisional
- Ontological claims are limited

Output JSON with: reification_detected (bool), severity (none/mild/moderate/severe), map_territory_confusion (what representation is confused with reality), model_as_reality (what model is treated as reality), abstraction_materialization (what abstraction is materialized), recommendation (no_reification/mild_construct_check/significant_abstraction_clarification/major_model_reassessment/emergency_complete_reification)."""

EPISTEMIC_METHODOLOGY_REIFICATION_PROMPT = """Detect epistemic methodology reification:

Construct concretization: {construct_concretization}
Map-territory confusion: {map_territory_confusion}
Model as reality: {model_as_reality}
Abstraction materialization: {abstraction_materialization}
Domain: {domain}
Context: {context}

Are abstract constructs being treated as concrete entities? Return ONLY valid JSON."""


class EpistemicMethodologyReificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        construct_concretization: str,
        *,
        map_territory_confusion: str = "",
        model_as_reality: str = "",
        abstraction_materialization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METHODOLOGY_REIFICATION_PROMPT.format(
                construct_concretization=construct_concretization,
                map_territory_confusion=map_territory_confusion or "Not specified",
                model_as_reality=model_as_reality or "Not specified",
                abstraction_materialization=abstraction_materialization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METHODOLOGY_REIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "construct_concretization": construct_concretization[:200],
            "reification_detected": data.get("reification_detected", False),
            "severity": data.get("severity", ""),
            "map_territory_confusion": data.get("map_territory_confusion", ""),
            "model_as_reality": data.get("model_as_reality", ""),
            "abstraction_materialization": data.get("abstraction_materialization", ""),
            "recommendation": data.get("recommendation", ""),
        }

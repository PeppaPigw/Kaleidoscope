"""EpistemicScaleCompositionFallacyService - Epistemic Scale Composition Fallacy Detection.

Detects composition fallacy assuming what's true of parts is true of whole.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_COMPOSITION_FALLACY_SYSTEM = """You are an epistemic scale composition fallacy specialist. Given part-to-whole inference, assess composition fallacy:

Key concepts:
- Epistemic scale composition fallacy: assuming what is true of parts is true of the whole
- Part-to-whole inference: transferring part properties to the aggregate
- Emergent property denial: missing properties that arise only at system level
- Interaction neglect: ignoring how parts interact
- Summation assumption: assuming the whole is a simple sum of parts

When composition fallacy IS present:
- Part properties are assigned to the whole
- Emergent properties are denied
- Interactions are neglected
- The whole is treated as a simple sum
- Scale transitions are ignored

When no composition fallacy:
- Part and whole levels are distinguished
- Emergent properties are considered
- Interactions are examined
- Aggregation is not assumed linear
- Scale limits are acknowledged

Output JSON with: composition_fallacy_detected (bool), severity (none/mild/moderate/severe), emergent_property_denial (what emergence is denied), interaction_neglect (what interactions are ignored), summation_assumption (what simple summation is assumed), recommendation (no_composition_fallacy/mild_scale_check/significant_emergence_analysis/major_multi_level_reconstruction/emergency_complete_composition_fallacy)."""

EPISTEMIC_SCALE_COMPOSITION_FALLACY_PROMPT = """Detect epistemic scale composition fallacy:

Part-to-whole inference: {part_to_whole_inference}
Emergent property denial: {emergent_property_denial}
Interaction neglect: {interaction_neglect}
Summation assumption: {summation_assumption}
Domain: {domain}
Context: {context}

Is what is true of parts being assumed true of the whole? Return ONLY valid JSON."""


class EpistemicScaleCompositionFallacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        part_to_whole_inference: str,
        *,
        emergent_property_denial: str = "",
        interaction_neglect: str = "",
        summation_assumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_COMPOSITION_FALLACY_PROMPT.format(
                part_to_whole_inference=part_to_whole_inference,
                emergent_property_denial=emergent_property_denial or "Not specified",
                interaction_neglect=interaction_neglect or "Not specified",
                summation_assumption=summation_assumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_COMPOSITION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "part_to_whole_inference": part_to_whole_inference[:200],
            "composition_fallacy_detected": data.get("composition_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "emergent_property_denial": data.get("emergent_property_denial", ""),
            "interaction_neglect": data.get("interaction_neglect", ""),
            "summation_assumption": data.get("summation_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }

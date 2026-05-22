"""CompositionFallacyService — Composition Fallacy Detection.

Detects composition fallacy — assuming that what is true of the parts
must be true of the whole. Individual properties don't necessarily
transfer to the aggregate. Each player being excellent doesn't make
the team excellent; each ingredient being healthy doesn't make the
meal healthy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPOSITION_FALLACY_SYSTEM = """You are a composition fallacy specialist. Given a reasoning pattern, assess whether properties of parts are being incorrectly attributed to the whole:

Key concepts:
- Composition fallacy: parts' properties ≠ whole's properties
- Emergent properties: wholes can have properties parts lack
- Aggregation error: individual truths don't sum to collective truth
- Ecological fallacy overlap: group properties ≠ individual properties
- Synergy/interference: parts interact in ways that change properties
- Level confusion: mixing levels of analysis
- Reductionism error: assuming whole is just sum of parts

When composition fallacy IS present:
- "Each part is X, therefore the whole is X"
- Assuming team quality equals sum of individual qualities
- Inferring system behavior from component behavior
- "Each step is safe, therefore the whole process is safe"
- Ignoring emergent properties and interactions
- "Each ingredient is cheap, so the dish is cheap"
- Treating complex systems as simple aggregates

When part-to-whole inference IS valid:
- The property genuinely transfers (e.g., each part is heavy → whole is heavy)
- No interactions between parts affect the property
- The inference is about additive properties
- The whole is genuinely just the sum of its parts for this property
- Emergent effects have been considered and ruled out
- The level of analysis is appropriate
- The property is preserved under composition

Output JSON with: composition_fallacy_present (bool), severity (none/mild/moderate/severe), parts (what parts are being considered), whole (what whole is being inferred about), property (what property is being transferred), interaction_effects (what interactions might change the property), emergent_properties (what might emerge at the whole level), recommendation (inference_valid/mild_aggregation_error/significant_composition_fallacy/major_level_confusion/consider_emergent_properties)."""

COMPOSITION_FALLACY_PROMPT = """Detect composition fallacy:

Reasoning: {reasoning}
Parts: {parts}
Whole: {whole}
Property: {property_attr}
Domain: {domain}
Context: {context}

Are properties of parts being incorrectly attributed to the whole? Return ONLY valid JSON."""


class CompositionFallacyService:
    """Detects composition fallacy — parts' properties ≠ whole's properties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        parts: str = "",
        whole: str = "",
        property_attr: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect composition fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPOSITION_FALLACY_PROMPT.format(
                reasoning=reasoning,
                parts=parts or "Not specified",
                whole=whole or "Not specified",
                property_attr=property_attr or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPOSITION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "composition_fallacy_present": data.get("composition_fallacy_present", False),
            "severity": data.get("severity", ""),
            "property": data.get("property", ""),
            "interaction_effects": data.get("interaction_effects", ""),
            "emergent_properties": data.get("emergent_properties", ""),
            "recommendation": data.get("recommendation", ""),
        }

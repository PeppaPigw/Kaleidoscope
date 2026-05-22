"""DivisionFallacyService — Division Fallacy Detection.

Detects division fallacy — assuming that what is true of the whole
must be true of each part. The inverse of composition fallacy.
A team being successful doesn't mean each member is successful;
a country being wealthy doesn't mean each citizen is wealthy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DIVISION_FALLACY_SYSTEM = """You are a division fallacy specialist. Given a reasoning pattern, assess whether properties of the whole are being incorrectly attributed to each part:

Key concepts:
- Division fallacy: whole's properties ≠ parts' properties
- Ecological fallacy overlap: group statistics ≠ individual properties
- Distribution error: aggregate properties don't distribute evenly
- Level confusion: inferring individual from collective
- Simpson's paradox: aggregate trends can reverse at individual level
- Heterogeneity: parts can differ greatly while whole has one property
- Statistical vs. individual: group averages don't describe individuals

When division fallacy IS present:
- "The whole is X, therefore each part is X"
- Assuming individual members share group properties
- "The company is profitable, so each division must be profitable"
- Inferring individual behavior from group statistics
- "Americans are wealthy" applied to each American
- Treating averages as if they apply to every case
- Ignoring variance and distribution within the whole

When whole-to-part inference IS valid:
- The property genuinely distributes (e.g., whole is made of iron → parts are iron)
- The property is definitional for membership
- Distribution is known to be uniform
- The inference acknowledges it's probabilistic, not certain
- The property is structural rather than statistical
- Individual variation has been considered
- The level of analysis is appropriate

Output JSON with: division_fallacy_present (bool), severity (none/mild/moderate/severe), whole (what whole is being considered), parts (what parts are being inferred about), property (what property is being distributed), distribution (how is the property actually distributed), variance (how much do parts vary), recommendation (inference_valid/mild_distribution_error/significant_division_fallacy/major_ecological_fallacy/consider_individual_variation)."""

DIVISION_FALLACY_PROMPT = """Detect division fallacy:

Reasoning: {reasoning}
Whole: {whole}
Parts: {parts}
Property: {property_attr}
Domain: {domain}
Context: {context}

Are properties of the whole being incorrectly attributed to each part? Return ONLY valid JSON."""


class DivisionFallacyService:
    """Detects division fallacy — whole's properties ≠ parts' properties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        whole: str = "",
        parts: str = "",
        property_attr: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect division fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DIVISION_FALLACY_PROMPT.format(
                reasoning=reasoning,
                whole=whole or "Not specified",
                parts=parts or "Not specified",
                property_attr=property_attr or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DIVISION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "division_fallacy_present": data.get("division_fallacy_present", False),
            "severity": data.get("severity", ""),
            "property": data.get("property", ""),
            "distribution": data.get("distribution", ""),
            "variance": data.get("variance", ""),
            "recommendation": data.get("recommendation", ""),
        }

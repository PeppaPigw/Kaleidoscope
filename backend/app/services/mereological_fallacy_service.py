"""MereologicalFallacyService — Mereological Fallacy Detection.

Detects mereological fallacy — attributing to parts properties that
can only meaningfully be attributed to the whole, or attributing to
the whole properties that only belong to parts. Bennett & Hacker (2003).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MEREOLOGICAL_SYSTEM = """You are a mereological fallacy specialist. Given a claim, assess whether it commits the mereological fallacy — confusing part-whole attribution:

Key concepts (Bennett & Hacker, 2003):
- Mereological fallacy: attributing to parts what belongs to wholes (or vice versa)
- Composition: inferring whole properties from part properties
- Division: inferring part properties from whole properties
- Category error: applying predicates to the wrong logical subject
- Emergent properties: properties of wholes not present in parts
- Reductionism: explaining wholes entirely in terms of parts
- Holism: properties that only exist at the system level

When mereological fallacy IS present:
- "The brain thinks" (thinking is a property of persons, not brains)
- "The company decided" when no collective decision process occurred
- Attributing consciousness to neurons rather than organisms
- "Society wants X" when only some members want X
- Treating a statistical property of a group as a property of each member
- "The gene is selfish" (genes don't have psychological properties)
- Confusing what a part does with what the whole does

When part-whole attribution IS appropriate:
- The property genuinely belongs at the attributed level
- Emergent properties are correctly attributed to the whole
- Mechanistic properties are correctly attributed to parts
- The attribution is metaphorical and acknowledged as such
- The level of description is appropriate for the explanation
- Causal contributions of parts are distinguished from properties of wholes
- The attribution is scientifically validated at that level

Output JSON with: mereological_fallacy_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), subject (what entity is attributed the property), property_attr (what property is attributed), correct_level (what level the property belongs to), direction (composition/division/neither), recommendation (attribution_appropriate/mild_level_confusion/significant_mereological_error/major_category_mistake/attribute_to_correct_level)."""

MEREOLOGICAL_PROMPT = """Detect mereological fallacy:

Claim: {claim}
Subject: {subject}
Property: {property_attr}
Level: {level}
Domain: {domain}
Context: {context}

Does this commit the mereological fallacy — attributing to parts what belongs to wholes or vice versa? Return ONLY valid JSON."""


class MereologicalFallacyService:
    """Detects mereological fallacy — part-whole attribution errors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        subject: str = "",
        property_attr: str = "",
        level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mereological fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MEREOLOGICAL_PROMPT.format(
                claim=claim,
                subject=subject or "Not specified",
                property_attr=property_attr or "Not specified",
                level=level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MEREOLOGICAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "mereological_fallacy_present": data.get("mereological_fallacy_present", False),
            "severity": data.get("severity", ""),
            "subject": data.get("subject", ""),
            "property_attr": data.get("property_attr", ""),
            "correct_level": data.get("correct_level", ""),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }

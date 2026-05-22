"""EpistemicAllergyService — Epistemic Allergy Detection.

Detects epistemic allergies — extreme reactions to specific idea
types regardless of their actual validity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ALLERGY_SYSTEM = """You are an epistemic allergy specialist. Given a knowledge system's response, assess whether extreme reactions occur to specific idea types regardless of validity:

Key concepts:
- Epistemic allergy: extreme reaction to specific idea types
- Validity-independent rejection: rejecting regardless of validity
- Trigger sensitivity: extreme sensitivity to specific triggers
- Categorical rejection: rejecting entire categories
- Learned aversion: learned extreme aversion to idea types
- Disproportionate response: response far exceeding threat
- Type-based rejection: rejecting based on type not content

When epistemic allergy IS present:
- Extreme reaction to specific idea types
- Rejecting regardless of actual validity
- Extreme sensitivity to specific intellectual triggers
- Rejecting entire categories without evaluation
- Learned extreme aversion to certain idea types
- Response far exceeding any actual threat
- Rejecting based on type rather than content

When appropriate skepticism is present:
- Skepticism proportionate to evidence
- Evaluation based on content not type
- Sensitivity calibrated to actual risk
- Categories evaluated individually
- Caution based on evidence not aversion
- Response proportionate to threat
- Judgment based on content and evidence

Output JSON with: allergy_present (bool), severity (none/mild/moderate/severe), system (what system is allergic), allergen (what idea type triggers reaction), reaction (what reaction occurs), validity (whether rejected ideas are actually invalid), recommendation (appropriate_skepticism/mild_aversion/significant_allergy/major_categorical_rejection/evaluate_on_merits)."""

EPISTEMIC_ALLERGY_PROMPT = """Detect epistemic allergy:

System: {system}
Allergen: {allergen}
Reaction: {reaction}
Validity: {validity}
Domain: {domain}
Context: {context}

Are extreme reactions occurring to specific idea types regardless of validity? Return ONLY valid JSON."""


class EpistemicAllergyService:
    """Detects epistemic allergies — extreme reactions regardless of validity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        allergen: str = "",
        reaction: str = "",
        validity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic allergy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ALLERGY_PROMPT.format(
                system=system,
                allergen=allergen or "Not specified",
                reaction=reaction or "Not specified",
                validity=validity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ALLERGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "allergy_present": data.get("allergy_present", False),
            "severity": data.get("severity", ""),
            "allergen": data.get("allergen", ""),
            "reaction": data.get("reaction", ""),
            "validity": data.get("validity", ""),
            "recommendation": data.get("recommendation", ""),
        }

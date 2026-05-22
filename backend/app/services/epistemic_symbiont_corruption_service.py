"""EpistemicSymbiontCorruptionService — Epistemic Symbiont Corruption Detection.

Detects epistemic symbiont corruption — formerly beneficial intellectual
relationships becoming parasitic.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SYMBIONT_CORRUPTION_SYSTEM = """You are an epistemic symbiont corruption specialist. Given an intellectual relationship, assess whether a formerly beneficial relationship has become parasitic:

Key concepts:
- Symbiont corruption: beneficial relationship becoming parasitic
- Mutualism collapse: mutual benefit collapsing to one-sided
- Trust exploitation: exploiting established trust
- Dependency creation: creating unhealthy dependency
- Benefit asymmetry: benefits becoming increasingly one-sided
- Relationship decay: relationship quality deteriorating
- Parasitic transition: transition from symbiosis to parasitism

When symbiont corruption IS present:
- Formerly beneficial relationship becoming parasitic
- Mutual benefit collapsing to one-sided extraction
- Exploiting trust established during beneficial phase
- Creating unhealthy intellectual dependency
- Benefits becoming increasingly one-sided
- Relationship quality deteriorating over time
- Clear transition from symbiosis to parasitism

When healthy symbiosis is present:
- Relationship maintaining mutual benefit
- Both parties gaining from exchange
- Trust appropriately maintained
- Healthy interdependence not dependency
- Benefits remaining balanced
- Relationship quality maintained or improving
- Genuine symbiosis continuing

Output JSON with: corruption_present (bool), severity (none/mild/moderate/severe), relationship (what relationship is corrupted), original_benefit (what original benefit existed), current_extraction (what extraction now occurs), transition (how transition happened), recommendation (healthy_symbiosis/mild_imbalance/significant_corruption/major_parasitic_transition/restore_mutualism)."""

EPISTEMIC_SYMBIONT_CORRUPTION_PROMPT = """Detect epistemic symbiont corruption:

Relationship: {relationship}
Original benefit: {original_benefit}
Current extraction: {current_extraction}
Transition: {transition}
Domain: {domain}
Context: {context}

Has a formerly beneficial intellectual relationship become parasitic? Return ONLY valid JSON."""


class EpistemicSymbiontCorruptionService:
    """Detects epistemic symbiont corruption — beneficial relationships becoming parasitic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        relationship: str,
        *,
        original_benefit: str = "",
        current_extraction: str = "",
        transition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic symbiont corruption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SYMBIONT_CORRUPTION_PROMPT.format(
                relationship=relationship,
                original_benefit=original_benefit or "Not specified",
                current_extraction=current_extraction or "Not specified",
                transition=transition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SYMBIONT_CORRUPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "relationship": relationship[:200],
            "corruption_present": data.get("corruption_present", False),
            "severity": data.get("severity", ""),
            "original_benefit": data.get("original_benefit", ""),
            "current_extraction": data.get("current_extraction", ""),
            "transition": data.get("transition", ""),
            "recommendation": data.get("recommendation", ""),
        }

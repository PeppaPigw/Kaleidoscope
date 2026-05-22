"""IsolatedDemandCharityService — Isolated Demand for Charity Detection.

Detects isolated demand for charity — demanding charitable
interpretation only for one's own side while interpreting the
other side uncharitably. The principle of charity (interpret
arguments in their strongest form) is applied asymmetrically:
"you're misrepresenting my position" while strawmanning theirs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ISOLATED_DEMAND_CHARITY_SYSTEM = """You are an isolated demand for charity specialist. Given a debate or disagreement, assess whether charitable interpretation is being demanded asymmetrically:

Key concepts:
- Principle of charity: interpret arguments in their strongest form
- Asymmetric charity: demanding charity for self, denying it to others
- Steelmanning vs strawmanning: strongest vs weakest interpretation
- "That's not what I meant" (for self) vs "that's exactly what they mean" (for others)
- Interpretive double standard: generous self-interpretation, hostile other-interpretation
- Motte-and-bailey interaction: retreating to charitable interpretation when challenged
- Good faith asymmetry: assuming own good faith, denying others'

When isolated demand for charity IS present:
- "You're taking me out of context" while taking others out of context
- Demanding steelman of own position while strawmanning opponents
- "That's not what I meant" for self, "that's exactly what they mean" for others
- Assuming own good faith while assuming others' bad faith
- Demanding nuanced reading of own words, literal reading of others'
- "You're being uncharitable" only when own position is challenged
- Different interpretive standards for in-group vs out-group

When charity demand IS appropriate:
- The same standard is applied to both sides
- The person also charitably interprets opposing views
- The misinterpretation is genuine and demonstrable
- Charitable interpretation is offered reciprocally
- The demand is for accuracy, not just favorability

Output JSON with: isolated_charity_present (bool), severity (none/mild/moderate/severe), own_interpretation (how does the person interpret their own words), other_interpretation (how do they interpret others' words), charity_demanded (what charitable reading is demanded for self), charity_denied (what charitable reading is denied to others), reciprocity (is charity applied symmetrically), double_standard (what is the interpretive double standard), recommendation (charity_reciprocal/mild_asymmetry/significant_isolated_charity/major_interpretive_double_standard/apply_charity_symmetrically)."""

ISOLATED_DEMAND_CHARITY_PROMPT = """Detect isolated demand for charity:

Debate: {debate}
Own position: {own_position}
Other position: {other_position}
Interpretation: {interpretation}
Domain: {domain}
Context: {context}

Is charitable interpretation being demanded asymmetrically — for one's own side but not the other? Return ONLY valid JSON."""


class IsolatedDemandCharityService:
    """Detects isolated demand for charity — asymmetric charitable interpretation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debate: str,
        *,
        own_position: str = "",
        other_position: str = "",
        interpretation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect isolated demand for charity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ISOLATED_DEMAND_CHARITY_PROMPT.format(
                debate=debate,
                own_position=own_position or "Not specified",
                other_position=other_position or "Not specified",
                interpretation=interpretation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ISOLATED_DEMAND_CHARITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debate": debate[:200],
            "isolated_charity_present": data.get("isolated_charity_present", False),
            "severity": data.get("severity", ""),
            "own_interpretation": data.get("own_interpretation", ""),
            "other_interpretation": data.get("other_interpretation", ""),
            "charity_demanded": data.get("charity_demanded", ""),
            "charity_denied": data.get("charity_denied", ""),
            "reciprocity": data.get("reciprocity", ""),
            "double_standard": data.get("double_standard", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicMetamorphosisService — Epistemic Metamorphosis Detection.

Detects epistemic metamorphosis — ideas undergoing complete
transformation through distinct developmental stages.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METAMORPHOSIS_SYSTEM = """You are an epistemic metamorphosis specialist. Given an idea development pattern, assess whether ideas undergo complete transformation through stages:

Key concepts:
- Epistemic metamorphosis: ideas transforming completely through stages
- Larval stage: early immature form of an idea
- Pupal stage: idea in transformation, neither old nor new form
- Adult stage: fully transformed mature idea
- Complete metamorphosis: total transformation between stages
- Incomplete metamorphosis: gradual change without distinct stages
- Imago: the final adult form of the transformed idea

When epistemic metamorphosis IS present:
- Ideas undergoing complete transformation through distinct stages
- Early immature forms of ideas clearly different from final form
- Ideas in transition, neither old nor new form
- Fully transformed ideas unrecognizable from their origins
- Total transformation between developmental stages
- Clear distinct stages in idea development
- Final form fundamentally different from initial form

When gradual development is present:
- Ideas developing gradually without distinct stages
- Early forms similar to later forms
- No transition period between forms
- Ideas recognizable throughout development
- Continuous change without transformation
- No distinct developmental stages
- Final form a natural extension of initial form

Output JSON with: metamorphosis_present (bool), severity (none/mild/moderate/severe), idea (what idea transforms), larval (what early form looks like), pupal (what transition looks like), adult (what final form looks like), recommendation (gradual_development/mild_transformation/significant_metamorphosis/major_complete_transformation/guide_through_stages)."""

EPISTEMIC_METAMORPHOSIS_PROMPT = """Detect epistemic metamorphosis:

Idea: {idea}
Larval: {larval}
Pupal: {pupal}
Adult: {adult}
Domain: {domain}
Context: {context}

Are ideas undergoing complete transformation through distinct developmental stages? Return ONLY valid JSON."""


class EpistemicMetamorphosisService:
    """Detects epistemic metamorphosis — complete idea transformation through stages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        larval: str = "",
        pupal: str = "",
        adult: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metamorphosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METAMORPHOSIS_PROMPT.format(
                idea=idea,
                larval=larval or "Not specified",
                pupal=pupal or "Not specified",
                adult=adult or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METAMORPHOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "metamorphosis_present": data.get("metamorphosis_present", False),
            "severity": data.get("severity", ""),
            "larval": data.get("larval", ""),
            "pupal": data.get("pupal", ""),
            "adult": data.get("adult", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicFreeloadingService — Epistemic Freeloading Detection.

Detects epistemic freeloading — benefiting from collective
knowledge production without contributing, relying on others'
epistemic labor while adding nothing to the knowledge commons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FREELOADING_SYSTEM = """You are an epistemic freeloading specialist. Given a knowledge community, assess whether freeloading is undermining collective knowledge:

Key concepts:
- Epistemic freeloading: benefiting without contributing
- Knowledge free-riding: using without producing
- Epistemic parasitism: extracting without adding
- Contribution asymmetry: some produce, many consume
- Commons depletion: freeloading degrading shared knowledge
- Reciprocity failure: taking without giving back
- Collective action problem: individual incentive to free-ride

When epistemic freeloading IS present:
- Benefits of collective knowledge taken without contribution
- Knowledge consumed but never produced
- Others' epistemic labor relied upon exclusively
- No reciprocal contribution to knowledge commons
- Freeloading degrades collective knowledge capacity
- Individual incentives favor free-riding
- Collective knowledge production undermined

When knowledge consumption is appropriate:
- Consumption proportional to capacity to contribute
- Contributions made in proportion to benefit
- Reciprocity maintained over time
- Knowledge commons sustained by participants
- Consumption enables future contribution
- Asymmetry temporary and acknowledged
- Collective capacity maintained

Output JSON with: freeloading_present (bool), severity (none/mild/moderate/severe), community (what community), consumption (what is consumed), contribution (what is contributed), asymmetry (what asymmetry exists), recommendation (appropriate_knowledge_consumption/mild_contribution_gap/significant_epistemic_freeloading/major_knowledge_parasitism/contribute_to_knowledge_commons)."""

EPISTEMIC_FREELOADING_PROMPT = """Detect epistemic freeloading:

Community: {community}
Knowledge consumed: {consumed}
Knowledge contributed: {contributed}
Reciprocity: {reciprocity}
Domain: {domain}
Context: {context}

Is someone benefiting from collective knowledge without contributing? Return ONLY valid JSON."""


class EpistemicFreeloadingService:
    """Detects epistemic freeloading — benefiting without contributing to knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        community: str,
        *,
        consumed: str = "",
        contributed: str = "",
        reciprocity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic freeloading."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FREELOADING_PROMPT.format(
                community=community,
                consumed=consumed or "Not specified",
                contributed=contributed or "Not specified",
                reciprocity=reciprocity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FREELOADING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "community": community[:200],
            "freeloading_present": data.get("freeloading_present", False),
            "severity": data.get("severity", ""),
            "consumption": data.get("consumption", ""),
            "contribution": data.get("contribution", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }

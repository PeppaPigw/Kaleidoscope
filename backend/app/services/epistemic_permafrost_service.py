"""EpistemicPermafrostService — Epistemic Permafrost Detection.

Detects epistemic permafrost — deeply frozen intellectual ground that
when thawed releases trapped ideas that may be toxic or destabilizing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERMAFROST_SYSTEM = """You are an epistemic permafrost specialist. Given a frozen knowledge pattern, assess whether thawing releases trapped toxic ideas:

Key concepts:
- Epistemic permafrost: deeply frozen intellectual ground
- Thaw: warming conditions releasing frozen ideas
- Trapped ideas: ideas preserved in frozen state for long time
- Methane release: toxic ideas released during thaw
- Ground instability: intellectual ground becoming unstable during thaw
- Active layer: thin surface layer that thaws seasonally
- Thermokarst: collapse features from thawing permafrost

When epistemic permafrost IS present:
- Deeply frozen intellectual ground containing trapped ideas
- Warming conditions beginning to thaw frozen knowledge
- Ideas preserved in frozen state for extended periods
- Toxic or destabilizing ideas released during thaw
- Intellectual ground becoming unstable as it thaws
- Only thin surface layer accessible while depths remain frozen
- Collapse features forming as frozen ground thaws

When accessible knowledge is present:
- Knowledge accessible and unfrozen throughout
- No warming/thawing dynamics
- Ideas freely available, not trapped
- No toxic releases from knowledge access
- Intellectual ground stable and solid
- All layers accessible
- No collapse risk from accessing knowledge

Output JSON with: permafrost_present (bool), severity (none/mild/moderate/severe), frozen_ground (what knowledge is frozen), thaw (what warming causes thaw), trapped_ideas (what ideas are released), toxicity (what toxic effects result), recommendation (accessible_knowledge/mild_thaw/significant_permafrost/major_toxic_release/controlled_thaw_with_containment)."""

EPISTEMIC_PERMAFROST_PROMPT = """Detect epistemic permafrost:

Frozen ground: {frozen_ground}
Thaw: {thaw}
Trapped ideas: {trapped_ideas}
Toxicity: {toxicity}
Domain: {domain}
Context: {context}

Is deeply frozen intellectual ground thawing and releasing trapped toxic or destabilizing ideas? Return ONLY valid JSON."""


class EpistemicPermafrostService:
    """Detects epistemic permafrost — frozen knowledge releasing toxic ideas when thawed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        frozen_ground: str,
        *,
        thaw: str = "",
        trapped_ideas: str = "",
        toxicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic permafrost."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERMAFROST_PROMPT.format(
                frozen_ground=frozen_ground,
                thaw=thaw or "Not specified",
                trapped_ideas=trapped_ideas or "Not specified",
                toxicity=toxicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERMAFROST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "frozen_ground": frozen_ground[:200],
            "permafrost_present": data.get("permafrost_present", False),
            "severity": data.get("severity", ""),
            "thaw": data.get("thaw", ""),
            "trapped_ideas": data.get("trapped_ideas", ""),
            "toxicity": data.get("toxicity", ""),
            "recommendation": data.get("recommendation", ""),
        }

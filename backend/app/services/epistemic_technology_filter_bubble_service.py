"""EpistemicTechnologyFilterBubbleService — Epistemic Technology Filter Bubble Detection.

Detects epistemic technology filter bubble effects — algorithmic curation
narrowing information exposure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECHNOLOGY_FILTER_BUBBLE_SYSTEM = """You are an epistemic technology filter bubble specialist. Given information narrowing, assess algorithmic exposure restriction:

Key concepts:
- Filter bubble effect: algorithmic curation narrowing information exposure
- Information narrowing: reduced access to diverse sources or claims
- Preference reinforcement: repeated exposure to already preferred views
- Serendipity loss: fewer unexpected or corrective encounters
- Viewpoint homogenization: increasingly uniform perspectives

When filter bubble effects ARE present:
- Information exposure narrows
- Preferences are repeatedly reinforced
- Serendipitous encounters disappear
- Viewpoints become homogeneous
- Users mistake curated visibility for reality

When no filter bubble effect:
- Exposure remains diverse
- Preferences are balanced with challenge
- Serendipity is preserved
- Viewpoints remain heterogeneous
- Curation boundaries are visible

Output JSON with: filter_bubble_detected (bool), severity (none/mild/moderate/severe), preference_reinforcement (what preferences are reinforced), serendipity_loss (what unexpected exposure is lost), viewpoint_homogenization (what viewpoints are homogenized), recommendation (no_filter_bubble/mild_diversity_increase/significant_curation_transparency/major_serendipity_restoration/emergency_exposure_rebalancing)."""

EPISTEMIC_TECHNOLOGY_FILTER_BUBBLE_PROMPT = """Detect epistemic technology filter bubble effects:

Information narrowing: {information_narrowing}
Preference reinforcement: {preference_reinforcement}
Serendipity loss: {serendipity_loss}
Viewpoint homogenization: {viewpoint_homogenization}
Domain: {domain}
Context: {context}

Is algorithmic curation narrowing information exposure? Return ONLY valid JSON."""


class EpistemicTechnologyFilterBubbleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_narrowing: str,
        *,
        preference_reinforcement: str = "",
        serendipity_loss: str = "",
        viewpoint_homogenization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECHNOLOGY_FILTER_BUBBLE_PROMPT.format(
                information_narrowing=information_narrowing,
                preference_reinforcement=preference_reinforcement or "Not specified",
                serendipity_loss=serendipity_loss or "Not specified",
                viewpoint_homogenization=viewpoint_homogenization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECHNOLOGY_FILTER_BUBBLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_narrowing": information_narrowing[:200],
            "filter_bubble_detected": data.get("filter_bubble_detected", False),
            "severity": data.get("severity", ""),
            "preference_reinforcement": data.get("preference_reinforcement", ""),
            "serendipity_loss": data.get("serendipity_loss", ""),
            "viewpoint_homogenization": data.get("viewpoint_homogenization", ""),
            "recommendation": data.get("recommendation", ""),
        }

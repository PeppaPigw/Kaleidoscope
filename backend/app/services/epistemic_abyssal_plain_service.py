"""EpistemicAbyssalPlainService — Epistemic Abyssal Plain Detection.

Detects epistemic abyssal plain — vast flat expanses of knowledge
where nothing stands out, making navigation and discovery impossible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABYSSAL_PLAIN_SYSTEM = """You are an epistemic abyssal plain specialist. Given a knowledge landscape, assess whether vast featureless expanses prevent navigation:

Key concepts:
- Epistemic abyssal plain: vast flat knowledge with no distinguishing features
- Featurelessness: no landmarks to navigate by
- Depth: knowledge too deep and uniform to explore
- Sediment: accumulated undifferentiated information
- Navigation failure: inability to find direction in uniform knowledge
- Monotony: intellectual monotony preventing engagement
- Benthic zone: the deepest layer where nothing is visible

When epistemic abyssal plain IS present:
- Vast flat expanses of knowledge with no distinguishing features
- No intellectual landmarks to navigate by
- Knowledge too deep and uniform to explore effectively
- Accumulated undifferentiated information covering everything
- Inability to find direction in uniform knowledge
- Intellectual monotony preventing engagement
- Deepest layers where nothing is visible or distinguishable

When navigable knowledge is present:
- Knowledge landscape with clear distinguishing features
- Intellectual landmarks available for navigation
- Knowledge at accessible depth with variation
- Information differentiated and organized
- Clear direction available in knowledge space
- Intellectual engagement maintained through variety
- All layers visible and distinguishable

Output JSON with: abyssal_plain_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is featureless), depth (how deep and uniform), sediment (what undifferentiated info accumulates), navigation (what navigation fails), recommendation (navigable_knowledge/mild_flatness/significant_featurelessness/major_navigation_failure/create_landmarks)."""

EPISTEMIC_ABYSSAL_PLAIN_PROMPT = """Detect epistemic abyssal plain:

Knowledge: {knowledge}
Depth: {depth}
Sediment: {sediment}
Navigation: {navigation}
Domain: {domain}
Context: {context}

Is knowledge a vast featureless expanse preventing navigation and discovery? Return ONLY valid JSON."""


class EpistemicAbyssalPlainService:
    """Detects epistemic abyssal plain — featureless knowledge preventing navigation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        depth: str = "",
        sediment: str = "",
        navigation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic abyssal plain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABYSSAL_PLAIN_PROMPT.format(
                knowledge=knowledge,
                depth=depth or "Not specified",
                sediment=sediment or "Not specified",
                navigation=navigation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABYSSAL_PLAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "abyssal_plain_present": data.get("abyssal_plain_present", False),
            "severity": data.get("severity", ""),
            "depth": data.get("depth", ""),
            "sediment": data.get("sediment", ""),
            "navigation": data.get("navigation", ""),
            "recommendation": data.get("recommendation", ""),
        }

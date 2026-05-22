"""EpistemicTerraIncognitaService — Epistemic Terra Incognita Detection.

Detects epistemic terra incognita — unknown territories being marked
as known, hiding ignorance behind false maps.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TERRA_INCOGNITA_SYSTEM = """You are an epistemic terra incognita specialist. Given a knowledge claim, assess whether unknown territory is being marked as known:

Key concepts:
- Epistemic terra incognita: unknown territories marked as known
- False mapping: creating maps of territory not actually explored
- Ignorance hiding: hiding ignorance behind confident claims
- Unexplored territory: areas not actually investigated
- Confidence without exploration: being confident without having explored
- Map without territory: having a map that doesn't correspond to reality
- Here be dragons: areas that should be marked unknown but aren't

When terra incognita IS present:
- Unknown territories being presented as known
- Maps created without actual exploration
- Ignorance hidden behind confident claims
- Areas not actually investigated presented as understood
- Confidence expressed without exploration
- Maps that don't correspond to actual territory
- Areas that should be marked unknown presented as known

When genuine knowledge is present:
- Known territories accurately represented
- Maps based on actual exploration
- Ignorance honestly acknowledged
- Areas actually investigated and understood
- Confidence proportionate to exploration
- Maps corresponding to actual territory
- Unknown areas honestly marked as unknown

Output JSON with: terra_incognita (bool), severity (none/mild/moderate/severe), territory (what unknown territory is claimed known), false_map (what false map is created), ignorance_hidden (what ignorance is hidden), exploration_gap (what exploration is missing), recommendation (genuine_knowledge/mild_overreach/significant_terra_incognita/major_false_mapping/acknowledge_unknowns)."""

EPISTEMIC_TERRA_INCOGNITA_PROMPT = """Detect epistemic terra incognita:

Territory: {territory}
False map: {false_map}
Ignorance hidden: {ignorance_hidden}
Exploration gap: {exploration_gap}
Domain: {domain}
Context: {context}

Is unknown territory being marked as known, hiding ignorance? Return ONLY valid JSON."""


class EpistemicTerraIncognitaService:
    """Detects epistemic terra incognita — unknown marked as known."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        territory: str,
        *,
        false_map: str = "",
        ignorance_hidden: str = "",
        exploration_gap: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic terra incognita."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TERRA_INCOGNITA_PROMPT.format(
                territory=territory,
                false_map=false_map or "Not specified",
                ignorance_hidden=ignorance_hidden or "Not specified",
                exploration_gap=exploration_gap or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TERRA_INCOGNITA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "territory": territory[:200],
            "terra_incognita": data.get("terra_incognita", False),
            "severity": data.get("severity", ""),
            "false_map": data.get("false_map", ""),
            "ignorance_hidden": data.get("ignorance_hidden", ""),
            "exploration_gap": data.get("exploration_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }

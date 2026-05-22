"""EpistemicLevelConfusionService — Epistemic Level Confusion Detection.

Detects epistemic level confusion — confusing levels of abstraction,
treating metaphors as literal or confusing map with territory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LEVEL_CONFUSION_SYSTEM = """You are an epistemic level confusion specialist. Given confusion between abstraction levels, assess level confusion:

Key concepts:
- Epistemic level confusion: confusing levels of abstraction
- Metaphor literalization: treating metaphors as literal claims
- Map-territory confusion: confusing the model with reality
- Category crossing: crossing category boundaries inappropriately
- Level mixing: mixing different levels of analysis
- Reification: treating abstractions as concrete things
- Type confusion: confusing types with tokens or vice versa

When epistemic level confusion IS present:
- Abstraction levels confused
- Metaphors taken literally
- Map confused with territory
- Categories crossed inappropriately
- Levels mixed
- Abstractions reified
- Types and tokens confused

When no level confusion:
- Abstraction levels clear
- Metaphors understood as metaphors
- Map distinguished from territory
- Categories respected
- Levels kept distinct
- Abstractions understood as abstractions
- Types and tokens distinguished

Output JSON with: level_confusion_detected (bool), severity (none/mild/moderate/severe), metaphor_literalization (what metaphors literalized), map_territory_confusion (what map-territory confused), category_crossing (what categories crossed), reification (what reified), recommendation (no_level_confusion/mild_level_awareness/significant_distinction_practice/major_intensive_level_clarity/emergency_complete_level_confusion)."""

EPISTEMIC_LEVEL_CONFUSION_PROMPT = """Detect epistemic level confusion:

Metaphor literalization: {metaphor_literalization}
Map-territory confusion: {map_territory_confusion}
Category crossing: {category_crossing}
Reification: {reification}
Domain: {domain}
Context: {context}

Are abstraction levels being confused? Return ONLY valid JSON."""


class EpistemicLevelConfusionService:
    """Detects epistemic level confusion — mixing abstraction levels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metaphor_literalization: str,
        *,
        map_territory_confusion: str = "",
        category_crossing: str = "",
        reification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic level confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LEVEL_CONFUSION_PROMPT.format(
                metaphor_literalization=metaphor_literalization,
                map_territory_confusion=map_territory_confusion or "Not specified",
                category_crossing=category_crossing or "Not specified",
                reification=reification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LEVEL_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metaphor_literalization": metaphor_literalization[:200],
            "level_confusion_detected": data.get("level_confusion_detected", False),
            "severity": data.get("severity", ""),
            "map_territory_confusion": data.get("map_territory_confusion", ""),
            "category_crossing": data.get("category_crossing", ""),
            "reification": data.get("reification", ""),
            "recommendation": data.get("recommendation", ""),
        }

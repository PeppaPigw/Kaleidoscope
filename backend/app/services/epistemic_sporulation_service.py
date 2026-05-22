"""EpistemicSporulationService — Epistemic Sporulation Detection.

Detects epistemic sporulation — ideas going dormant and dispersing
as resistant spores when conditions become hostile.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPORULATION_SYSTEM = """You are an epistemic sporulation specialist. Given an idea survival pattern, assess whether ideas are going dormant as resistant spores:

Key concepts:
- Epistemic sporulation: ideas going dormant as resistant spores
- Dormancy: ideas becoming inactive but not dead
- Dispersal: dormant ideas spreading to new environments
- Resistance: spores surviving hostile conditions
- Germination: dormant ideas reactivating when conditions improve
- Trigger: what causes ideas to sporulate
- Viability: how long dormant ideas remain viable

When epistemic sporulation IS present:
- Ideas going dormant in response to hostile conditions
- Ideas becoming inactive but maintaining viability
- Dormant ideas dispersing to new intellectual environments
- Ideas surviving hostile conditions in dormant form
- Potential for reactivation when conditions improve
- Clear trigger causing ideas to go dormant
- Ideas maintaining viability during dormancy

When active ideas are present:
- Ideas remaining active and growing
- No dormancy in response to conditions
- Ideas staying in their current environment
- Ideas thriving in current conditions
- No need for dormancy or dispersal
- Conditions supporting active growth
- Ideas fully expressed and developing

Output JSON with: sporulation_present (bool), severity (none/mild/moderate/severe), ideas (what ideas sporulate), trigger (what triggers dormancy), dispersal (where spores spread), viability (how long they remain viable), recommendation (active_ideas/mild_dormancy/significant_sporulation/major_dispersal/improve_conditions_for_germination)."""

EPISTEMIC_SPORULATION_PROMPT = """Detect epistemic sporulation:

Ideas: {ideas}
Trigger: {trigger}
Dispersal: {dispersal}
Viability: {viability}
Domain: {domain}
Context: {context}

Are ideas going dormant and dispersing as resistant spores due to hostile conditions? Return ONLY valid JSON."""


class EpistemicSporulationService:
    """Detects epistemic sporulation — ideas going dormant as resistant spores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        trigger: str = "",
        dispersal: str = "",
        viability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sporulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPORULATION_PROMPT.format(
                ideas=ideas,
                trigger=trigger or "Not specified",
                dispersal=dispersal or "Not specified",
                viability=viability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPORULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "sporulation_present": data.get("sporulation_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "dispersal": data.get("dispersal", ""),
            "viability": data.get("viability", ""),
            "recommendation": data.get("recommendation", ""),
        }

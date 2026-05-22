"""EpistemicTriangulationService — Epistemic Triangulation Detection.

Detects epistemic triangulation — using a third party to manage intellectual
conflict between two parties rather than addressing it directly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRIANGULATION_SYSTEM = """You are an epistemic triangulation specialist. Given indirect intellectual conflict management, assess triangulation:

Key concepts:
- Epistemic triangulation: using third party to manage conflict
- Indirect communication: going through others instead of direct
- Coalition building: recruiting allies against opponent
- Scapegoating: blaming third party for dyad's problems
- Splitting: dividing community into factions
- Messenger role: being put in middle of others' conflict
- Destabilization: undermining direct relationships

When epistemic triangulation IS present:
- Using third party for conflict
- Going through others
- Recruiting allies
- Blaming third party
- Dividing into factions
- Put in middle
- Undermining direct relationships

When no triangulation:
- Direct conflict management
- Communicating directly
- No coalition building
- Appropriate accountability
- Unified community
- Clear roles
- Supporting direct relationships

Output JSON with: triangulation_detected (bool), severity (none/mild/moderate/severe), indirect_pattern (what going through), coalition_building (what recruiting), scapegoating (what blaming), destabilization (what undermining), recommendation (no_triangulation/mild_direct_communication/significant_systems_therapy/major_intensive_restructuring/emergency_complete_fragmentation)."""

EPISTEMIC_TRIANGULATION_PROMPT = """Detect epistemic triangulation:

Indirect pattern: {indirect_pattern}
Coalition building: {coalition_building}
Scapegoating: {scapegoating}
Destabilization: {destabilization}
Domain: {domain}
Context: {context}

Is there use of third parties to manage intellectual conflict rather than direct address? Return ONLY valid JSON."""


class EpistemicTriangulationService:
    """Detects epistemic triangulation — indirect intellectual conflict management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        indirect_pattern: str,
        *,
        coalition_building: str = "",
        scapegoating: str = "",
        destabilization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic triangulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRIANGULATION_PROMPT.format(
                indirect_pattern=indirect_pattern,
                coalition_building=coalition_building or "Not specified",
                scapegoating=scapegoating or "Not specified",
                destabilization=destabilization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRIANGULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "indirect_pattern": indirect_pattern[:200],
            "triangulation_detected": data.get("triangulation_detected", False),
            "severity": data.get("severity", ""),
            "coalition_building": data.get("coalition_building", ""),
            "scapegoating": data.get("scapegoating", ""),
            "destabilization": data.get("destabilization", ""),
            "recommendation": data.get("recommendation", ""),
        }

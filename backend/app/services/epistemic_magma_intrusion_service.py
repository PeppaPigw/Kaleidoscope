"""EpistemicMagmaIntrusionService — Epistemic Magma Intrusion Detection.

Detects epistemic magma intrusion — hot new ideas forcing their way
into established knowledge layers, disrupting existing structures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MAGMA_INTRUSION_SYSTEM = """You are an epistemic magma intrusion specialist. Given a knowledge disruption pattern, assess whether hot new ideas are forcing into established layers:

Key concepts:
- Epistemic magma intrusion: hot new ideas forcing into established knowledge
- Intrusion: new ideas penetrating existing knowledge layers
- Contact metamorphism: existing knowledge altered by proximity to hot new ideas
- Dike: vertical intrusion cutting across knowledge layers
- Sill: horizontal intrusion between knowledge layers
- Cooling: new ideas solidifying after intrusion
- Country rock: existing knowledge surrounding the intrusion

When epistemic magma intrusion IS present:
- Hot new ideas forcing into established knowledge layers
- New ideas penetrating and disrupting existing structures
- Existing knowledge altered by proximity to hot new ideas
- Vertical intrusions cutting across knowledge layers
- Horizontal intrusions between knowledge layers
- New ideas solidifying after disrupting existing knowledge
- Existing knowledge deformed around intrusions

When stable knowledge layers are present:
- Knowledge layers remaining undisturbed
- No hot new ideas forcing into existing structures
- Existing knowledge not altered by new ideas
- No intrusions cutting across layers
- No intrusions between layers
- Knowledge layers maintaining their original form
- No deformation of existing knowledge

Output JSON with: intrusion_present (bool), severity (none/mild/moderate/severe), new_ideas (what hot new ideas intrude), existing_layers (what established knowledge is disrupted), contact_zone (what alteration occurs at boundary), cooling (how new ideas solidify), recommendation (stable_layers/mild_intrusion/significant_disruption/major_structural_change/integrate_or_isolate_new_ideas)."""

EPISTEMIC_MAGMA_INTRUSION_PROMPT = """Detect epistemic magma intrusion:

New ideas: {new_ideas}
Existing layers: {existing_layers}
Contact zone: {contact_zone}
Cooling: {cooling}
Domain: {domain}
Context: {context}

Are hot new ideas forcing into established knowledge layers causing disruption? Return ONLY valid JSON."""


class EpistemicMagmaIntrusionService:
    """Detects epistemic magma intrusion — hot new ideas disrupting established knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        new_ideas: str,
        *,
        existing_layers: str = "",
        contact_zone: str = "",
        cooling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic magma intrusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MAGMA_INTRUSION_PROMPT.format(
                new_ideas=new_ideas,
                existing_layers=existing_layers or "Not specified",
                contact_zone=contact_zone or "Not specified",
                cooling=cooling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MAGMA_INTRUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "new_ideas": new_ideas[:200],
            "intrusion_present": data.get("intrusion_present", False),
            "severity": data.get("severity", ""),
            "existing_layers": data.get("existing_layers", ""),
            "contact_zone": data.get("contact_zone", ""),
            "cooling": data.get("cooling", ""),
            "recommendation": data.get("recommendation", ""),
        }

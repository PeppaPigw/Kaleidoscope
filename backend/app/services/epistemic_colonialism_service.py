"""EpistemicColonialismService — Epistemic Colonialism Detection.

Detects epistemic colonialism — imposing one knowledge system
as universal while suppressing or devaluing indigenous and local
knowledge systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLONIALISM_SYSTEM = """You are an epistemic colonialism specialist. Given a knowledge interaction, assess whether one knowledge system is being imposed as universal:

Key concepts:
- Epistemic colonialism: imposing one knowledge system as universal
- Knowledge hierarchy: ranking knowledge systems by power not merit
- Indigenous knowledge suppression: devaluing local ways of knowing
- Universalism as imperialism: treating local knowledge as universal
- Epistemic violence: destroying other knowledge systems
- Cognitive imperialism: imposing categories of thought
- Knowledge extraction: taking without attribution or reciprocity

When epistemic colonialism IS present:
- One knowledge system imposed as universal standard
- Local/indigenous knowledge devalued or suppressed
- Power determines which knowledge counts
- Categories of one system imposed on others
- Knowledge extracted without reciprocity
- Alternative epistemologies dismissed as primitive
- Universality claimed for particular knowledge

When knowledge sharing is appropriate:
- Knowledge shared with respect and reciprocity
- Multiple knowledge systems recognized as valid
- Universality claims based on evidence not power
- Local knowledge valued and preserved
- Exchange is mutual and voluntary
- Different epistemologies in dialogue
- Power dynamics acknowledged

Output JSON with: colonialism_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), imposed (what knowledge system is imposed), suppressed (what is suppressed), mechanism (how imposition works), recommendation (appropriate_knowledge_sharing/mild_epistemic_hierarchy/significant_epistemic_colonialism/major_knowledge_imperialism/decolonize_knowledge)."""

EPISTEMIC_COLONIALISM_PROMPT = """Detect epistemic colonialism:

Situation: {situation}
Knowledge imposed: {imposed}
Knowledge suppressed: {suppressed}
Power dynamics: {power}
Domain: {domain}
Context: {context}

Is one knowledge system being imposed as universal while suppressing others? Return ONLY valid JSON."""


class EpistemicColonialismService:
    """Detects epistemic colonialism — imposing one knowledge system as universal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        imposed: str = "",
        suppressed: str = "",
        power: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic colonialism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLONIALISM_PROMPT.format(
                situation=situation,
                imposed=imposed or "Not specified",
                suppressed=suppressed or "Not specified",
                power=power or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLONIALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "colonialism_present": data.get("colonialism_present", False),
            "severity": data.get("severity", ""),
            "imposed": data.get("imposed", ""),
            "suppressed": data.get("suppressed", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }

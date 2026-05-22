"""EpistemicInvasiveSpeciesService — Epistemic Invasive Species Detection.

Detects epistemic invasive species — foreign frameworks colonizing
and displacing native understanding without adaptation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INVASIVE_SPECIES_SYSTEM = """You are an epistemic invasive species specialist. Given a knowledge domain, assess whether foreign frameworks are colonizing and displacing native understanding:

Key concepts:
- Epistemic invasive species: foreign frameworks displacing native understanding
- Framework colonization: imported frameworks taking over local knowledge
- Native displacement: local understanding displaced by imports
- Inappropriate transplant: frameworks applied outside their native context
- Ecological disruption: disruption of existing knowledge ecosystem
- Adaptation failure: imported frameworks not adapted to local context
- Monoculture imposition: single framework imposed on diverse contexts

When epistemic invasive species IS present:
- Foreign frameworks colonizing local knowledge space
- Imported frameworks displacing native understanding
- Local understanding displaced without good reason
- Frameworks applied outside their appropriate context
- Existing knowledge ecosystem disrupted
- Imported frameworks not adapted to local needs
- Single framework imposed on diverse contexts

When healthy cross-pollination is present:
- Foreign ideas adapted to local context
- Imports enriching rather than displacing
- Local understanding strengthened by new perspectives
- Frameworks appropriately adapted before application
- Ecosystem enriched by diversity
- Imports integrated with existing knowledge
- Multiple frameworks coexisting productively

Output JSON with: invasive_species_present (bool), severity (none/mild/moderate/severe), domain (what domain is affected), invader (what framework is invasive), displaced (what native understanding is displaced), adaptation (whether adaptation occurred), recommendation (healthy_cross_pollination/mild_displacement/significant_invasive_species/major_framework_colonization/adapt_before_importing)."""

EPISTEMIC_INVASIVE_SPECIES_PROMPT = """Detect epistemic invasive species:

Domain: {target_domain}
Invader: {invader}
Displaced: {displaced}
Adaptation: {adaptation}
Field: {field}
Context: {context}

Are foreign frameworks colonizing and displacing native understanding? Return ONLY valid JSON."""


class EpistemicInvasiveSpeciesService:
    """Detects epistemic invasive species — foreign frameworks displacing native understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target_domain: str,
        *,
        invader: str = "",
        displaced: str = "",
        adaptation: str = "",
        field: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic invasive species."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INVASIVE_SPECIES_PROMPT.format(
                target_domain=target_domain,
                invader=invader or "Not specified",
                displaced=displaced or "Not specified",
                adaptation=adaptation or "Not specified",
                field=field or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INVASIVE_SPECIES_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target_domain": target_domain[:200],
            "invasive_species_present": data.get("invasive_species_present", False),
            "severity": data.get("severity", ""),
            "invader": data.get("invader", ""),
            "displaced": data.get("displaced", ""),
            "adaptation": data.get("adaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }

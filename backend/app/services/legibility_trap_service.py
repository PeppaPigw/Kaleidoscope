"""LegibilityTrapService — Legibility Trap Detection.

Identifies when making a system "legible" (measurable, standardized,
simplified for top-down control) destroys the properties that made
it work. James C. Scott's concept — scientific forestry that killed
forests, urban planning that killed neighborhoods, standardization
that eliminates adaptive local knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LEGIBILITY_SYSTEM = """You are a legibility trap specialist. Given a system being made more legible (measurable, standardized, simplified), assess whether legibility is destroying value:
- Is simplification eliminating important complexity?
- Is standardization destroying adaptive local knowledge (metis)?
- Is measurement changing the behavior of what's being measured?
- Is top-down control replacing bottom-up adaptation?
- Is the map being confused with the territory?

Output JSON with: legibility_trap_present (bool), severity (none/mild/moderate/severe/catastrophic), system_being_simplified (what is being made legible), simplification_method (how it's being standardized/measured), what_gets_lost (what valuable properties are destroyed by legibility), metis_destroyed (local/tacit knowledge being eliminated), who_demands_legibility (who benefits from the simplification), who_loses_from_legibility (who suffers when complexity is eliminated), map_territory_confusion (bool — is the simplified model being treated as reality?), goodhart_overlap (bool — is measurement changing behavior?), high_modernist_ideology (bool — is there faith that rational planning can replace organic complexity?), historical_parallels (similar legibility disasters), illegible_but_functional (what works precisely because it's complex/messy/local), resilience_lost (what adaptive capacity is destroyed), reversibility (can the original complexity be restored?), recommendation (legibility_appropriate/preserve_illegibility/partial_legibility/resist_simplification)."""

LEGIBILITY_PROMPT = """Detect legibility traps:

System: {system}
Simplification being applied: {simplification}
Purpose of legibility: {purpose}
Local knowledge at risk: {local_knowledge}
Domain: {domain}
Context: {context}

Is legibility destroying value? Return ONLY valid JSON."""


class LegibilityTrapService:
    """Detects legibility traps — simplification destroying value."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        simplification: str = "",
        purpose: str = "",
        local_knowledge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect legibility traps."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LEGIBILITY_PROMPT.format(
                system=system,
                simplification=simplification or "Not specified",
                purpose=purpose or "Not specified",
                local_knowledge=local_knowledge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LEGIBILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "legibility_trap_present": data.get("legibility_trap_present", False),
            "severity": data.get("severity", ""),
            "system_being_simplified": data.get("system_being_simplified", ""),
            "simplification_method": data.get("simplification_method", ""),
            "what_gets_lost": data.get("what_gets_lost", ""),
            "metis_destroyed": data.get("metis_destroyed", ""),
            "who_demands_legibility": data.get("who_demands_legibility", ""),
            "who_loses_from_legibility": data.get("who_loses_from_legibility", ""),
            "map_territory_confusion": data.get("map_territory_confusion", False),
            "goodhart_overlap": data.get("goodhart_overlap", False),
            "high_modernist_ideology": data.get("high_modernist_ideology", False),
            "historical_parallels": data.get("historical_parallels", []),
            "illegible_but_functional": data.get("illegible_but_functional", ""),
            "resilience_lost": data.get("resilience_lost", ""),
            "reversibility": data.get("reversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }

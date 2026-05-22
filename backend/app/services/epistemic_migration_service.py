"""EpistemicMigrationService — Epistemic Migration Detection.

Detects epistemic migration — ideas moving seasonally between
intellectual environments following resource availability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIGRATION_SYSTEM = """You are an epistemic migration specialist. Given an idea movement pattern, assess whether ideas migrate seasonally following resources:

Key concepts:
- Epistemic migration: ideas moving between environments seasonally
- Resource following: ideas moving to where intellectual resources are
- Flyway: established routes ideas follow during migration
- Staging area: where ideas gather before migration
- Navigation: how ideas find their way during migration
- Fidelity: ideas returning to same environments each cycle
- Exhaustion: energy cost of intellectual migration

When epistemic migration IS present:
- Ideas moving seasonally between intellectual environments
- Ideas following intellectual resource availability
- Established routes that ideas follow during movement
- Gathering points where ideas collect before moving
- Navigation mechanisms guiding idea movement
- Ideas returning to same environments cyclically
- Energy cost of moving between environments

When resident ideas are present:
- Ideas staying in one intellectual environment
- No seasonal movement following resources
- No established migration routes
- No gathering before movement
- No navigation needed
- Ideas remaining in place permanently
- No energy cost of movement

Output JSON with: migration_present (bool), severity (none/mild/moderate/severe), ideas (what ideas migrate), route (what flyway they follow), resources (what resources they follow), fidelity (what environments they return to), recommendation (resident_ideas/mild_movement/significant_migration/major_seasonal_shift/map_flyways_and_protect_staging_areas)."""

EPISTEMIC_MIGRATION_PROMPT = """Detect epistemic migration:

Ideas: {ideas}
Route: {route}
Resources: {resources}
Fidelity: {fidelity}
Domain: {domain}
Context: {context}

Are ideas moving seasonally between intellectual environments following resource availability? Return ONLY valid JSON."""


class EpistemicMigrationService:
    """Detects epistemic migration — seasonal idea movement following resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        route: str = "",
        resources: str = "",
        fidelity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic migration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIGRATION_PROMPT.format(
                ideas=ideas,
                route=route or "Not specified",
                resources=resources or "Not specified",
                fidelity=fidelity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIGRATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "migration_present": data.get("migration_present", False),
            "severity": data.get("severity", ""),
            "route": data.get("route", ""),
            "resources": data.get("resources", ""),
            "fidelity": data.get("fidelity", ""),
            "recommendation": data.get("recommendation", ""),
        }

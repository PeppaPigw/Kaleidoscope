"""CollectiveIgnoranceMaintenanceService — Collective Ignorance Maintenance Detection.

Detects collective ignorance maintenance — groups maintaining collective
ignorance to avoid collective responsibility, where shared not-knowing
serves as a group defense mechanism.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COLLECTIVE_IGNORANCE_MAINTENANCE_SYSTEM = """You are a collective ignorance maintenance specialist. Given a group knowledge situation, assess whether collective ignorance is being maintained:

Key concepts:
- Collective ignorance maintenance: group maintaining shared not-knowing
- Shared ignorance as defense: group ignorance avoiding group responsibility
- Taboo knowledge: things the group agrees not to know
- Collective willful blindness: group choosing not to see
- Institutional ignorance: organizations maintaining not-knowing
- Conspiracy of silence: agreement to not know or discuss
- Knowledge suppression: group suppressing available knowledge

When collective ignorance maintenance IS present:
- Group maintaining shared ignorance
- Collective not-knowing serving as defense
- Knowledge available but collectively avoided
- Taboo against knowing certain things
- Institutional structures maintaining ignorance
- Agreement (explicit or implicit) to not know
- Group responsibility avoided through shared ignorance

When appropriate collective boundaries are present:
- Group knowledge boundaries serving legitimate purposes
- Collective focus appropriately bounded
- Not-knowing incidental not maintained
- Group responsibility acknowledged despite knowledge limits
- Institutional boundaries serving function not avoidance
- Knowledge limits honest not strategic
- Collective ignorance recognized as problem not maintained

Output JSON with: maintenance_present (bool), severity (none/mild/moderate/severe), group (what group is involved), ignorance_maintained (what ignorance is maintained), responsibility_avoided (what responsibility is avoided), mechanism (how ignorance is maintained), recommendation (appropriate_boundaries/mild_collective_avoidance/significant_ignorance_maintenance/major_collective_willful_blindness/break_collective_ignorance_patterns)."""

COLLECTIVE_IGNORANCE_MAINTENANCE_PROMPT = """Detect collective ignorance maintenance:

Group situation: {situation}
Knowledge available: {available}
Knowledge avoided: {avoided}
Group dynamics: {dynamics}
Domain: {domain}
Context: {context}

Is a group maintaining collective ignorance to avoid collective responsibility? Return ONLY valid JSON."""


class CollectiveIgnoranceMaintenanceService:
    """Detects collective ignorance maintenance — groups maintaining shared not-knowing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        available: str = "",
        avoided: str = "",
        dynamics: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect collective ignorance maintenance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COLLECTIVE_IGNORANCE_MAINTENANCE_PROMPT.format(
                situation=situation,
                available=available or "Not specified",
                avoided=avoided or "Not specified",
                dynamics=dynamics or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COLLECTIVE_IGNORANCE_MAINTENANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "maintenance_present": data.get("maintenance_present", False),
            "severity": data.get("severity", ""),
            "ignorance_maintained": data.get("ignorance_maintained", ""),
            "responsibility_avoided": data.get("responsibility_avoided", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }

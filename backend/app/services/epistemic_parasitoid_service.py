"""EpistemicParasitoidService — Epistemic Parasitoid Detection.

Detects epistemic parasitoids — ideas that develop inside host ideas,
eventually consuming and destroying them from within.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARASITOID_SYSTEM = """You are an epistemic parasitoid specialist. Given an idea relationship, assess whether one idea is developing inside another to eventually destroy it:

Key concepts:
- Epistemic parasitoid: idea developing inside host to destroy it
- Oviposition: parasitoid idea being planted inside host idea
- Larval development: parasitoid growing inside host undetected
- Host consumption: parasitoid consuming host from within
- Emergence: parasitoid bursting out of consumed host
- Host manipulation: parasitoid altering host behavior for its benefit
- Specificity: parasitoid targeting specific types of host ideas

When epistemic parasitoid IS present:
- One idea developing inside another idea
- Parasitoid idea planted inside host idea
- Parasitoid growing inside host undetected
- Host idea being consumed from within
- Parasitoid eventually destroying and replacing host
- Host idea's behavior altered by internal parasitoid
- Parasitoid targeting specific types of host ideas

When independent ideas are present:
- Ideas developing independently
- No ideas planted inside others
- No hidden internal development
- Ideas not being consumed from within
- Ideas maintaining their integrity
- Ideas behaving according to their own nature
- No targeting of specific idea types

Output JSON with: parasitoid_present (bool), severity (none/mild/moderate/severe), parasitoid (what idea is the parasitoid), host (what idea is the host), development (what internal development occurs), consumption (what consumption happens), recommendation (independent_ideas/mild_influence/significant_parasitoid/major_host_destruction/remove_parasitoid_protect_host)."""

EPISTEMIC_PARASITOID_PROMPT = """Detect epistemic parasitoid:

Parasitoid: {parasitoid}
Host: {host}
Development: {development}
Consumption: {consumption}
Domain: {domain}
Context: {context}

Is one idea developing inside another to eventually consume and destroy it from within? Return ONLY valid JSON."""


class EpistemicParasitoidService:
    """Detects epistemic parasitoid — ideas consuming hosts from within."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        parasitoid: str,
        *,
        host: str = "",
        development: str = "",
        consumption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic parasitoid."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARASITOID_PROMPT.format(
                parasitoid=parasitoid,
                host=host or "Not specified",
                development=development or "Not specified",
                consumption=consumption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARASITOID_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "parasitoid": parasitoid[:200],
            "parasitoid_present": data.get("parasitoid_present", False),
            "severity": data.get("severity", ""),
            "host": data.get("host", ""),
            "development": data.get("development", ""),
            "consumption": data.get("consumption", ""),
            "recommendation": data.get("recommendation", ""),
        }

"""EpistemicExternalityService — Epistemic Externality Detection.

Detects epistemic externalities — hidden costs of belief production
or consumption borne by third parties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXTERNALITY_SYSTEM = """You are an epistemic externality specialist. Given a belief production pattern, assess whether hidden costs are borne by third parties:

Key concepts:
- Epistemic externality: hidden costs borne by third parties
- Negative externality: harm to others from belief production
- Cost displacement: costs displaced onto uninvolved parties
- Pollution analogy: belief production polluting epistemic commons
- Unpriced harm: harm not accounted for by producers
- Third-party damage: damage to uninvolved third parties
- Commons degradation: degradation of shared epistemic resources

When epistemic externality IS present:
- Hidden costs of belief production borne by third parties
- Harm to others from belief production or consumption
- Costs displaced onto uninvolved parties
- Belief production polluting the epistemic commons
- Harm not accounted for by those producing it
- Damage to uninvolved third parties
- Shared epistemic resources degraded

When internalized costs is present:
- Costs of belief production borne by producers
- No harm displaced to third parties
- Costs appropriately accounted for
- Epistemic commons maintained
- Harm accounted for by producers
- Third parties not damaged
- Shared resources maintained

Output JSON with: externality_present (bool), severity (none/mild/moderate/severe), production (what belief production causes externality), cost (what cost is externalized), third_party (who bears the cost), commons_damage (what commons damage occurs), recommendation (internalized_costs/mild_externality/significant_externality/major_commons_damage/internalize_costs)."""

EPISTEMIC_EXTERNALITY_PROMPT = """Detect epistemic externality:

Production: {production}
Cost: {cost}
Third party: {third_party}
Commons damage: {commons_damage}
Domain: {domain}
Context: {context}

Are hidden costs of belief production being borne by third parties? Return ONLY valid JSON."""


class EpistemicExternalityService:
    """Detects epistemic externalities — hidden costs borne by third parties."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        production: str,
        *,
        cost: str = "",
        third_party: str = "",
        commons_damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic externality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXTERNALITY_PROMPT.format(
                production=production,
                cost=cost or "Not specified",
                third_party=third_party or "Not specified",
                commons_damage=commons_damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXTERNALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "production": production[:200],
            "externality_present": data.get("externality_present", False),
            "severity": data.get("severity", ""),
            "cost": data.get("cost", ""),
            "third_party": data.get("third_party", ""),
            "commons_damage": data.get("commons_damage", ""),
            "recommendation": data.get("recommendation", ""),
        }

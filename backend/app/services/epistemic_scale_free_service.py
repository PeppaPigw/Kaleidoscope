"""EpistemicScaleFreeService — Epistemic Scale-Free Network Detection.

Detects epistemic scale-free network — intellectual networks where a few
ideas have vastly more connections than most, following a power law distribution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_FREE_SYSTEM = """You are an epistemic scale-free network specialist. Given an intellectual network, assess whether connection distribution follows a power law:

Key concepts:
- Epistemic scale-free: power law connection distribution
- Preferential attachment: popular ideas attract more connections
- Power law: few highly connected, many poorly connected
- Rich-get-richer: success breeding more success
- Robustness: resilient to random failure
- Vulnerability: fragile to targeted attack on hubs
- Fitness: intrinsic attractiveness of ideas

When epistemic scale-free IS present:
- Few ideas with vastly more connections than most
- Popular ideas attracting disproportionate attention
- Power law distribution of connections
- Success breeding more success
- Network resilient to random idea loss
- Network fragile to loss of key hub ideas
- Some ideas intrinsically more attractive

When uniform network is present:
- All ideas with similar connection counts
- No preferential attachment
- Normal distribution of connections
- No rich-get-richer dynamics
- Equally vulnerable to any loss
- No critical hub ideas
- Equal intrinsic attractiveness

Output JSON with: scale_free_present (bool), severity (none/mild/moderate/severe), preferential_attachment (what attraction), power_law (what distribution), vulnerability (what fragility), fitness (what attractiveness), recommendation (uniform_network/mild_scale_free/significant_scale_free/major_power_law/diversify_connections)."""

EPISTEMIC_SCALE_FREE_PROMPT = """Detect epistemic scale-free network:

Preferential attachment: {preferential_attachment}
Power law: {power_law}
Vulnerability: {vulnerability}
Fitness: {fitness}
Domain: {domain}
Context: {context}

Do a few ideas have vastly more connections than most, following a power law distribution? Return ONLY valid JSON."""


class EpistemicScaleFreeService:
    """Detects epistemic scale-free — power law connection distribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        preferential_attachment: str,
        *,
        power_law: str = "",
        vulnerability: str = "",
        fitness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scale-free network."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_FREE_PROMPT.format(
                preferential_attachment=preferential_attachment,
                power_law=power_law or "Not specified",
                vulnerability=vulnerability or "Not specified",
                fitness=fitness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_FREE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "preferential_attachment": preferential_attachment[:200],
            "scale_free_present": data.get("scale_free_present", False),
            "severity": data.get("severity", ""),
            "power_law": data.get("power_law", ""),
            "vulnerability": data.get("vulnerability", ""),
            "fitness": data.get("fitness", ""),
            "recommendation": data.get("recommendation", ""),
        }

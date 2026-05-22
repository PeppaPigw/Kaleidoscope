"""EpistemicCommonsTragedyService — Epistemic Commons Tragedy Detection.

Detects epistemic commons tragedy — tragedy of the commons in shared
epistemic resources, where individual incentives degrade shared
knowledge infrastructure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMONS_TRAGEDY_SYSTEM = """You are an epistemic commons tragedy specialist. Given a shared epistemic resource situation, assess whether commons tragedy dynamics are present:

Key concepts:
- Epistemic commons tragedy: shared knowledge resources degraded by individual incentives
- Free-riding on trust: exploiting shared trust without maintaining it
- Knowledge commons depletion: shared knowledge resources being depleted
- Incentive misalignment: individual incentives degrading shared resources
- Trust erosion: individual actions eroding collective trust
- Quality race to bottom: competition degrading shared quality standards
- Collective action failure: inability to maintain shared epistemic goods

When epistemic commons tragedy IS present:
- Individual incentives degrading shared epistemic resources
- Free-riding on collective trust without maintaining it
- Shared knowledge resources being depleted
- Competition driving quality downward
- Individual actions eroding collective epistemic goods
- Inability to coordinate maintenance of shared resources
- Short-term individual gain at long-term collective cost

When appropriate resource use is present:
- Individual and collective incentives aligned
- Shared resources maintained by participants
- Trust actively maintained alongside use
- Quality standards upheld collectively
- Individual actions supporting shared goods
- Coordination maintaining epistemic commons
- Long-term collective benefit considered

Output JSON with: tragedy_present (bool), severity (none/mild/moderate/severe), commons (what shared resource is affected), individual_incentive (what individual incentive drives degradation), collective_cost (what collective cost results), mechanism (how tragedy unfolds), recommendation (aligned_incentives/mild_free_riding/significant_commons_tragedy/major_epistemic_resource_depletion/align_incentives_with_commons_maintenance)."""

EPISTEMIC_COMMONS_TRAGEDY_PROMPT = """Detect epistemic commons tragedy:

Shared resource: {resource}
Individual incentives: {incentives}
Collective impact: {impact}
Coordination: {coordination}
Domain: {domain}
Context: {context}

Are individual incentives degrading shared epistemic resources? Return ONLY valid JSON."""


class EpistemicCommonsTragedyService:
    """Detects epistemic commons tragedy — individual incentives degrading shared resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        resource: str,
        *,
        incentives: str = "",
        impact: str = "",
        coordination: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic commons tragedy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMONS_TRAGEDY_PROMPT.format(
                resource=resource,
                incentives=incentives or "Not specified",
                impact=impact or "Not specified",
                coordination=coordination or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMONS_TRAGEDY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "resource": resource[:200],
            "tragedy_present": data.get("tragedy_present", False),
            "severity": data.get("severity", ""),
            "individual_incentive": data.get("individual_incentive", ""),
            "collective_cost": data.get("collective_cost", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }

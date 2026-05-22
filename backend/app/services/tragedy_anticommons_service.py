"""TragedyAnticommonsService — Tragedy of the Anticommons Detection.

Detects tragedy of the anticommons — when too many parties hold
exclusion rights over a resource, leading to underuse because any
party can block use. Heller (1998). The mirror image of the tragedy
of the commons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRAGEDY_ANTICOMMONS_SYSTEM = """You are a tragedy of the anticommons specialist. Given a resource governance situation, assess whether too many veto holders are causing underuse:

Key concepts (Heller, 1998):
- Tragedy of the anticommons: too many exclusion rights → underuse
- Veto players: parties who can block use of a resource
- Holdout problem: each party can extract rents by threatening to block
- Patent thicket: overlapping IP rights preventing innovation
- Fragmented ownership: too many parties must agree for action
- Transaction costs: coordination costs exceed value of use
- Mirror of commons: commons = overuse, anticommons = underuse

When anticommons IS present:
- Multiple parties can independently block use of a resource
- Valuable resources go unused because coordination is too costly
- Each veto holder demands payment, making total cost prohibitive
- Innovation is blocked by overlapping rights
- Decision-making requires unanimous consent from too many parties
- Holdout behavior prevents efficient resource allocation
- The resource would be used if ownership were consolidated

When multiple rights holders ARE appropriate:
- Checks and balances serve a legitimate governance purpose
- The veto structure prevents harmful overuse
- Transaction costs are manageable
- Coordination mechanisms exist and function
- The fragmentation serves diversity or safety goals
- Rights holders actively cooperate
- The resource is being used at an appropriate level

Output JSON with: anticommons_present (bool), severity (none/mild/moderate/severe), resource (what resource is affected), veto_holders (who can block), underuse (evidence of underuse), coordination_cost (cost of getting agreement), holdout_behavior (is holdout occurring), recommendation (governance_appropriate/mild_fragmentation/significant_anticommons/major_resource_underuse/consolidate_or_coordinate)."""

TRAGEDY_ANTICOMMONS_PROMPT = """Detect tragedy of the anticommons:

Resource: {resource}
Governance: {governance}
Veto holders: {veto_holders}
Underuse evidence: {underuse}
Domain: {domain}
Context: {context}

Are too many veto holders causing underuse of this resource? Return ONLY valid JSON."""


class TragedyAnticommonsService:
    """Detects tragedy of the anticommons — too many veto holders causing underuse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        resource: str,
        *,
        governance: str = "",
        veto_holders: str = "",
        underuse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tragedy of the anticommons."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRAGEDY_ANTICOMMONS_PROMPT.format(
                resource=resource,
                governance=governance or "Not specified",
                veto_holders=veto_holders or "Not specified",
                underuse=underuse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TRAGEDY_ANTICOMMONS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "resource": resource[:200],
            "anticommons_present": data.get("anticommons_present", False),
            "severity": data.get("severity", ""),
            "veto_holders": data.get("veto_holders", ""),
            "underuse": data.get("underuse", ""),
            "coordination_cost": data.get("coordination_cost", ""),
            "holdout_behavior": data.get("holdout_behavior", ""),
            "recommendation": data.get("recommendation", ""),
        }

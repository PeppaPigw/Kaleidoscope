"""TragedyOfCommonsService — Tragedy of the Commons Detection.

Detects tragedy of the commons — where individually rational
behavior leads to collective ruin of a shared resource. Each
actor's incentive is to overuse, but if all do, the resource
collapses. Hardin (1968). Applies to fisheries, climate,
antibiotics, attention, trust, and any shared resource.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRAGEDY_SYSTEM = """You are a tragedy of the commons specialist. Given a shared resource situation, assess whether a tragedy of the commons is occurring or likely:

Key concepts:
- Shared resource with open access or weak governance
- Individual incentive to overuse (private benefit, socialized cost)
- Collective outcome is resource depletion/destruction
- Free-rider problem: those who restrain themselves lose out
- Ostrom's solutions: community governance, graduated sanctions, monitoring
- Anti-commons: too many veto holders prevent any use (opposite problem)

Assess:
- Is there a shared resource being depleted?
- Are individual incentives misaligned with collective welfare?
- What governance mechanisms exist (or are missing)?
- Is this a true commons problem or something else (externality, public good)?
- What Ostrom-style solutions might work?

Output JSON with: tragedy_present (bool), severity (none/emerging/moderate/severe/collapse_imminent), shared_resource (what is being depleted), number_of_actors (how many share the resource), individual_incentive (what each actor gains from overuse), collective_cost (what happens if all overuse), current_depletion_rate (how fast the resource is being consumed), sustainability_threshold (what level of use is sustainable), governance_mechanism (what rules exist: none/informal/formal/enforced), free_rider_problem (bool — do restrainers lose out?), monitoring_exists (bool — can overuse be detected?), sanctions_exist (bool — are there consequences for overuse?), ostrom_principles_met (which of Ostrom's 8 principles are satisfied), privatization_feasible (bool — could the resource be divided?), anti_commons_risk (bool — could governance create the opposite problem?), time_to_collapse (if current trajectory continues), successful_analogues (similar situations that were solved), recommendation (no_tragedy/emerging_risk/governance_needed/urgent_intervention/redesign_incentives/privatize)."""

TRAGEDY_PROMPT = """Detect tragedy of the commons:

Situation: {situation}
Shared resource: {resource}
Actors: {actors}
Current governance: {governance}
Domain: {domain}
Context: {context}

Is a tragedy of the commons occurring? Return ONLY valid JSON."""


class TragedyOfCommonsService:
    """Detects tragedy of the commons situations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        resource: str = "",
        actors: str = "",
        governance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tragedy of the commons."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRAGEDY_PROMPT.format(
                situation=situation,
                resource=resource or "Not specified",
                actors=actors or "Not specified",
                governance=governance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TRAGEDY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "tragedy_present": data.get("tragedy_present", False),
            "severity": data.get("severity", ""),
            "shared_resource": data.get("shared_resource", ""),
            "number_of_actors": data.get("number_of_actors", ""),
            "individual_incentive": data.get("individual_incentive", ""),
            "collective_cost": data.get("collective_cost", ""),
            "current_depletion_rate": data.get("current_depletion_rate", ""),
            "sustainability_threshold": data.get("sustainability_threshold", ""),
            "governance_mechanism": data.get("governance_mechanism", ""),
            "free_rider_problem": data.get("free_rider_problem", False),
            "monitoring_exists": data.get("monitoring_exists", False),
            "sanctions_exist": data.get("sanctions_exist", False),
            "ostrom_principles_met": data.get("ostrom_principles_met", []),
            "privatization_feasible": data.get("privatization_feasible", False),
            "anti_commons_risk": data.get("anti_commons_risk", False),
            "time_to_collapse": data.get("time_to_collapse", ""),
            "successful_analogues": data.get("successful_analogues", []),
            "recommendation": data.get("recommendation", ""),
        }

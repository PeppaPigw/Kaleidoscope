"""CollectiveActionService — Collective Action Problem Detection.

Identifies when individually rational behavior leads to collectively
irrational outcomes. Tragedy of the commons, free-rider problems,
coordination failures, prisoner's dilemmas — situations where
everyone acting in self-interest produces worse outcomes for all.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COLLECTIVE_SYSTEM = """You are a collective action problem specialist. Given a situation, assess whether a collective action problem exists:
- Are individuals acting rationally but producing collectively bad outcomes?
- Is there a free-rider problem (benefiting without contributing)?
- Is there a tragedy of the commons (overusing shared resources)?
- Is there a coordination failure (everyone would benefit from cooperation but can't coordinate)?
- Is there a prisoner's dilemma structure (mutual defection despite mutual cooperation being better)?

Output JSON with: collective_action_problem (bool), severity (none/mild/moderate/severe/critical), problem_type (tragedy_of_commons/free_rider/coordination_failure/prisoners_dilemma/race_to_bottom/collective_inaction), individual_incentive (what each actor is rationally motivated to do), collective_outcome (what happens when everyone follows individual incentive), optimal_outcome (what would happen with perfect cooperation), gap_size (how far the actual outcome is from optimal: small/moderate/large/catastrophic), number_of_actors (few/many/massive), excludability (can non-contributors be excluded from benefits?), rivalry (does one person's use reduce availability for others?), trust_level (how much actors trust each other: none/low/moderate/high), communication_possible (bool — can actors coordinate?), enforcement_available (bool — can agreements be enforced?), existing_solutions (mechanisms already in place), missing_solutions (mechanisms that could help: regulation/privatization/social_norms/technology/incentive_design), tipping_point (what would shift behavior toward cooperation), recommendation (design_incentives/enable_coordination/regulate/privatize/accept_suboptimal)."""

COLLECTIVE_PROMPT = """Detect collective action problems:

Situation: {situation}
Actors: {actors}
Shared resource/goal: {shared_resource}
Current behavior: {current_behavior}
Domain: {domain}
Context: {context}

Is there a collective action problem? Return ONLY valid JSON."""


class CollectiveActionService:
    """Detects collective action problems and coordination failures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        actors: str = "",
        shared_resource: str = "",
        current_behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect collective action problems."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COLLECTIVE_PROMPT.format(
                situation=situation,
                actors=actors or "Not specified",
                shared_resource=shared_resource or "Not specified",
                current_behavior=current_behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COLLECTIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "collective_action_problem": data.get("collective_action_problem", False),
            "severity": data.get("severity", ""),
            "problem_type": data.get("problem_type", ""),
            "individual_incentive": data.get("individual_incentive", ""),
            "collective_outcome": data.get("collective_outcome", ""),
            "optimal_outcome": data.get("optimal_outcome", ""),
            "gap_size": data.get("gap_size", ""),
            "number_of_actors": data.get("number_of_actors", ""),
            "excludability": data.get("excludability", ""),
            "rivalry": data.get("rivalry", ""),
            "trust_level": data.get("trust_level", ""),
            "communication_possible": data.get("communication_possible", False),
            "enforcement_available": data.get("enforcement_available", False),
            "existing_solutions": data.get("existing_solutions", ""),
            "missing_solutions": data.get("missing_solutions", ""),
            "tipping_point": data.get("tipping_point", ""),
            "recommendation": data.get("recommendation", ""),
        }

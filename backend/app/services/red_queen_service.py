"""RedQueenService — Red Queen Effect Detection.

Detects the Red Queen Effect — competitive dynamics where
participants must keep running (investing, innovating, adapting)
just to maintain their current position. From Lewis Carroll:
"It takes all the running you can do, to keep in the same place."
Van Valen (1973) in evolutionary biology. Applies to arms races,
technology competition, credential inflation, and regulatory
cat-and-mouse games.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RED_QUEEN_SYSTEM = """You are a Red Queen Effect specialist. Given a competitive situation, assess whether Red Queen dynamics are forcing participants to run just to stay in place:

Key concepts (Van Valen, 1973):
- Red Queen Effect: continuous adaptation required just to maintain fitness
- Arms race: each side's improvement neutralizes the other's
- Credential inflation: everyone gets degrees → degrees become worthless
- Feature creep: competitors add features → baseline expectations rise
- Treadmill effect: effort increases but relative position stays the same
- Escalation trap: can't stop without falling behind

Examples:
- Education: more people get MBAs → MBA becomes minimum requirement
- Cybersecurity: better defenses → better attacks → better defenses
- Advertising: everyone advertises more → no one gains market share
- Working hours: everyone works longer → baseline expectation rises
- Technology: faster hardware → bloated software → need faster hardware

When Red Queen dynamics ARE present:
- Increasing effort/investment with no improvement in relative position
- Competitive escalation where stopping means falling behind
- Rising baselines that neutralize individual improvements
- Arms race dynamics with no stable equilibrium
- Collective action problem: everyone would benefit from stopping

When competition IS productive:
- Improvements create genuine new value (not just relative advantage)
- There's a natural ceiling or equilibrium
- Competition drives innovation that benefits consumers/society
- Participants can opt out without catastrophic consequences

Output JSON with: red_queen_present (bool), severity (none/mild/moderate/severe), competition_type (what kind of competitive dynamic), escalation_pattern (how the arms race is escalating), baseline_shift (how the minimum requirement has risen), effort_vs_position (how much more effort for same relative position), value_created (is genuine value being created or just relative positioning?), collective_action_problem (bool — would everyone benefit from stopping?), exit_possible (bool — can participants opt out?), exit_cost (what happens if you stop competing), equilibrium_exists (bool — is there a natural stopping point?), who_benefits (who gains from the escalation), who_loses (who is harmed by the treadmill), waste_generated (what resources are consumed without creating value), breaking_strategy (how to escape the Red Queen trap), recommendation (competition_productive/mild_escalation/significant_red_queen/severe_arms_race/collective_action_needed)."""

RED_QUEEN_PROMPT = """Detect Red Queen Effect:

Situation: {situation}
Competition: {competition}
Escalation history: {escalation}
Current baseline: {baseline}
Domain: {domain}
Context: {context}

Are Red Queen dynamics forcing participants to run just to stay in place? Return ONLY valid JSON."""


class RedQueenService:
    """Detects Red Queen Effect — competitive treadmill where running maintains position."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        competition: str = "",
        escalation: str = "",
        baseline: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Red Queen Effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RED_QUEEN_PROMPT.format(
                situation=situation,
                competition=competition or "Not specified",
                escalation=escalation or "Not specified",
                baseline=baseline or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RED_QUEEN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "red_queen_present": data.get("red_queen_present", False),
            "severity": data.get("severity", ""),
            "competition_type": data.get("competition_type", ""),
            "escalation_pattern": data.get("escalation_pattern", ""),
            "baseline_shift": data.get("baseline_shift", ""),
            "effort_vs_position": data.get("effort_vs_position", ""),
            "value_created": data.get("value_created", ""),
            "collective_action_problem": data.get("collective_action_problem", False),
            "exit_possible": data.get("exit_possible", False),
            "exit_cost": data.get("exit_cost", ""),
            "equilibrium_exists": data.get("equilibrium_exists", False),
            "who_benefits": data.get("who_benefits", ""),
            "who_loses": data.get("who_loses", ""),
            "waste_generated": data.get("waste_generated", ""),
            "breaking_strategy": data.get("breaking_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }

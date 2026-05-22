"""RaceToBottomService — Race to the Bottom Detection.

Detects race-to-the-bottom dynamics — competitive pressure driving
standards, prices, wages, regulations, or quality downward as
participants undercut each other. Each actor's individually
rational choice produces collectively irrational outcomes.
Related to prisoner's dilemma and collective action problems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RACE_BOTTOM_SYSTEM = """You are a race-to-the-bottom specialist. Given a competitive situation, assess whether race-to-the-bottom dynamics are degrading standards:

Key concepts:
- Race to the bottom: competition drives standards/prices/quality downward
- Regulatory arbitrage: moving to jurisdictions with weakest rules
- Price war: competitors undercut until margins disappear
- Quality erosion: cutting corners to compete on price
- Labor arbitrage: seeking cheapest workers regardless of conditions
- Environmental dumping: competing by externalizing costs
- Collective action failure: everyone would benefit from a floor, but no one can unilaterally stop

When race to the bottom IS present:
- Competitors are undercutting each other on price/standards/quality
- The "winning" strategy involves degrading something valuable
- Externalities are being shifted to third parties
- A floor or minimum standard would benefit all participants
- Individual rationality produces collective irrationality

When competitive pressure IS healthy:
- Competition drives genuine efficiency improvements
- Quality is maintained while costs decrease through innovation
- Consumers benefit without third-party harm
- There's a natural floor (can't go below zero cost)
- Differentiation on quality remains viable

Output JSON with: race_to_bottom_present (bool), severity (none/mild/moderate/severe), competition_type (what's being competed on), what_is_degrading (what standard/quality/price is falling), mechanism (how undercutting works), externalities (who bears the costs), individually_rational (bool — is each actor's choice rational in isolation?), collectively_irrational (bool — is the outcome bad for everyone?), floor_needed (what minimum standard would help), coordination_possible (bool — could participants agree to stop?), regulatory_gap (what governance is missing), who_benefits_short_term (who gains from the race), who_loses_long_term (who is harmed over time), equilibrium (where does the race end?), intervention_options (how to stop the race), recommendation (competition_healthy/mild_pressure/significant_race_to_bottom/severe_standards_erosion/establish_floor_urgently)."""

RACE_BOTTOM_PROMPT = """Detect race to the bottom:

Situation: {situation}
Competition: {competition}
Standards affected: {standards}
Participants: {participants}
Domain: {domain}
Context: {context}

Are race-to-the-bottom dynamics degrading standards? Return ONLY valid JSON."""


class RaceToBottomService:
    """Detects race to the bottom — competitive pressure degrading standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        competition: str = "",
        standards: str = "",
        participants: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect race to the bottom."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RACE_BOTTOM_PROMPT.format(
                situation=situation,
                competition=competition or "Not specified",
                standards=standards or "Not specified",
                participants=participants or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RACE_BOTTOM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "race_to_bottom_present": data.get("race_to_bottom_present", False),
            "severity": data.get("severity", ""),
            "competition_type": data.get("competition_type", ""),
            "what_is_degrading": data.get("what_is_degrading", ""),
            "mechanism": data.get("mechanism", ""),
            "externalities": data.get("externalities", ""),
            "individually_rational": data.get("individually_rational", False),
            "collectively_irrational": data.get("collectively_irrational", False),
            "floor_needed": data.get("floor_needed", ""),
            "coordination_possible": data.get("coordination_possible", False),
            "regulatory_gap": data.get("regulatory_gap", ""),
            "who_benefits_short_term": data.get("who_benefits_short_term", ""),
            "who_loses_long_term": data.get("who_loses_long_term", ""),
            "equilibrium": data.get("equilibrium", ""),
            "intervention_options": data.get("intervention_options", ""),
            "recommendation": data.get("recommendation", ""),
        }

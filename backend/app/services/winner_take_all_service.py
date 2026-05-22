"""WinnerTakeAllService — Winner-Take-All Detection.

Detects winner-take-all dynamics — situations where small
differences in performance or luck produce disproportionately
large differences in reward. Frank & Cook (1995). Network
effects, platform economics, and tournament structures create
markets where #1 gets everything and #2 gets nothing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WINNER_SYSTEM = """You are a winner-take-all dynamics specialist. Given a competitive situation, assess whether winner-take-all effects are creating disproportionate outcomes:

Key concepts (Frank & Cook, 1995):
- Winner-take-all: small performance differences → huge reward differences
- Network effects: value increases with users → natural monopoly
- Platform economics: two-sided markets tip to one dominant platform
- Tournament structure: only the winner gets the prize
- Superstar economics: Rosen (1981) — technology amplifies small talent differences
- Power law distribution: outcomes follow Pareto rather than normal distribution
- Lock-in: switching costs prevent movement even when alternatives are better

When winner-take-all IS present:
- Small differences in quality/timing produce huge outcome gaps
- Markets tip toward one dominant player
- Network effects create self-reinforcing advantages
- Second place gets dramatically less than first
- Luck plays a large role in who ends up on top
- Barriers to entry grow as the winner accumulates advantage

When proportional rewards ARE appropriate:
- Rewards scale linearly with contribution
- Multiple viable competitors can coexist
- No network effects or lock-in
- Quality differences are large and meaningful
- Markets are contestable (low barriers to entry)

Output JSON with: winner_take_all_present (bool), severity (none/mild/moderate/severe), market_structure (how the competitive landscape is organized), performance_gap (how different are the top competitors?), reward_gap (how different are the rewards?), disproportionality (ratio of reward difference to performance difference), network_effects (bool — do network effects amplify advantages?), platform_tipping (bool — is the market tipping to one player?), lock_in (bool — are switching costs preventing competition?), luck_vs_skill (how much of the outcome is luck vs genuine superiority?), barriers_to_entry (what prevents new competitors), contestability (bool — can the winner be displaced?), social_cost (what value is lost from winner-take-all dynamics), alternative_structure (how could rewards be more proportional), recommendation (rewards_proportional/mild_concentration/significant_winner_take_all/severe_market_tipping/restructure_incentives)."""

WINNER_PROMPT = """Detect winner-take-all dynamics:

Situation: {situation}
Market/Competition: {market}
Reward structure: {rewards}
Network effects: {network_effects}
Domain: {domain}
Context: {context}

Are winner-take-all dynamics creating disproportionate outcomes? Return ONLY valid JSON."""


class WinnerTakeAllService:
    """Detects winner-take-all dynamics — small differences producing huge reward gaps."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        market: str = "",
        rewards: str = "",
        network_effects: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect winner-take-all dynamics."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WINNER_PROMPT.format(
                situation=situation,
                market=market or "Not specified",
                rewards=rewards or "Not specified",
                network_effects=network_effects or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WINNER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "winner_take_all_present": data.get("winner_take_all_present", False),
            "severity": data.get("severity", ""),
            "market_structure": data.get("market_structure", ""),
            "performance_gap": data.get("performance_gap", ""),
            "reward_gap": data.get("reward_gap", ""),
            "disproportionality": data.get("disproportionality", ""),
            "network_effects": data.get("network_effects", False),
            "platform_tipping": data.get("platform_tipping", False),
            "lock_in": data.get("lock_in", False),
            "luck_vs_skill": data.get("luck_vs_skill", ""),
            "barriers_to_entry": data.get("barriers_to_entry", ""),
            "contestability": data.get("contestability", False),
            "social_cost": data.get("social_cost", ""),
            "alternative_structure": data.get("alternative_structure", ""),
            "recommendation": data.get("recommendation", ""),
        }

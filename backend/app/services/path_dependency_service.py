"""PathDependencyService — Path Dependency Analysis.

Identifies when current options are constrained by historical choices
that may no longer be optimal. QWERTY keyboards, VHS over Betamax,
legacy tech stacks — understanding when you're locked in, what
switching costs look like, and whether the lock-in is still rational.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PATH_DEP_SYSTEM = """You are a path dependency specialist. Given a situation, assess whether path dependency is constraining current options:
- Are current choices limited by historical decisions?
- Would you make the same choice if starting from scratch today?
- What are the switching costs to a better alternative?
- Is the lock-in getting stronger or weaker over time?
- Are there increasing returns that reinforce the current path?

Output JSON with: path_dependency_present (bool), severity (none/mild/moderate/severe/locked_in), original_choice (the historical decision creating the dependency), original_context (why it made sense at the time), current_constraint (how it limits options today), better_alternative (what you'd choose if starting fresh), switching_cost (low/moderate/high/prohibitive), switching_cost_breakdown (what makes switching expensive: technical/social/financial/regulatory), increasing_returns (bool — does staying on path get more attractive over time?), network_effects (bool — does value depend on others being on same path?), lock_in_strengthening (bool — is the dependency getting harder to escape?), window_of_opportunity (is there a moment when switching becomes easier?), sunk_cost_trap (bool — is sunk cost fallacy keeping you on this path?), rational_to_stay (bool — given switching costs, is staying actually optimal?), breaking_strategy (how to escape if desired: gradual_migration/clean_break/parallel_systems/wait_for_disruption), recommendation (stay_on_path/plan_migration/break_now/wait_for_window)."""

PATH_DEP_PROMPT = """Analyze path dependency:

Situation: {situation}
Current state: {current_state}
Historical choice: {historical_choice}
Alternatives considered: {alternatives}
Domain: {domain}
Context: {context}

Is path dependency constraining options? Return ONLY valid JSON."""


class PathDependencyService:
    """Analyzes path dependency and lock-in effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        situation: str,
        *,
        current_state: str = "",
        historical_choice: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze path dependency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PATH_DEP_PROMPT.format(
                situation=situation,
                current_state=current_state or "Not specified",
                historical_choice=historical_choice or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PATH_DEP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "path_dependency_present": data.get("path_dependency_present", False),
            "severity": data.get("severity", ""),
            "original_choice": data.get("original_choice", ""),
            "original_context": data.get("original_context", ""),
            "current_constraint": data.get("current_constraint", ""),
            "better_alternative": data.get("better_alternative", ""),
            "switching_cost": data.get("switching_cost", ""),
            "switching_cost_breakdown": data.get("switching_cost_breakdown", ""),
            "increasing_returns": data.get("increasing_returns", False),
            "network_effects": data.get("network_effects", False),
            "lock_in_strengthening": data.get("lock_in_strengthening", False),
            "window_of_opportunity": data.get("window_of_opportunity", ""),
            "sunk_cost_trap": data.get("sunk_cost_trap", False),
            "rational_to_stay": data.get("rational_to_stay", False),
            "breaking_strategy": data.get("breaking_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }

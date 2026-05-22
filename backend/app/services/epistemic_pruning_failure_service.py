"""EpistemicPruningFailureService — Epistemic Pruning Failure Detection.

Detects epistemic pruning failure — dead intellectual branches not
removed, consuming resources that could support living growth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRUNING_FAILURE_SYSTEM = """You are an epistemic pruning failure specialist. Given a knowledge system, assess whether dead branches consume resources:

Key concepts:
- Epistemic pruning failure: dead branches not removed
- Resource consumption: dead ideas consuming intellectual resources
- Dead wood: ideas that no longer produce value
- Growth obstruction: dead branches blocking new growth
- Maintenance burden: cost of maintaining dead ideas
- Decay spread: dead branches spreading decay to living ones
- Selective removal: need to identify and remove dead branches

When pruning failure IS present:
- Dead intellectual branches not removed
- Obsolete ideas consuming resources
- Ideas that no longer produce value maintained
- Dead branches blocking new intellectual growth
- High cost of maintaining dead ideas
- Decay from dead ideas spreading to living ones
- Need to identify and remove dead branches

When proper pruning is present:
- Dead branches regularly identified and removed
- Resources directed to productive ideas
- Only value-producing ideas maintained
- New growth unobstructed by dead wood
- Low maintenance burden
- No decay spreading from dead ideas
- Regular identification and removal of dead branches

Output JSON with: pruning_failure (bool), severity (none/mild/moderate/severe), dead_branches (what dead branches exist), resources_consumed (what resources are wasted), growth_blocked (what growth is blocked), decay_spread (what decay spreads), recommendation (proper_pruning/mild_dead_wood/significant_pruning_failure/major_resource_waste/identify_and_remove)."""

EPISTEMIC_PRUNING_FAILURE_PROMPT = """Detect epistemic pruning failure:

Dead branches: {dead_branches}
Resources consumed: {resources_consumed}
Growth blocked: {growth_blocked}
Decay spread: {decay_spread}
Domain: {domain}
Context: {context}

Are dead intellectual branches consuming resources and blocking new growth? Return ONLY valid JSON."""


class EpistemicPruningFailureService:
    """Detects epistemic pruning failure — dead branches consuming resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dead_branches: str,
        *,
        resources_consumed: str = "",
        growth_blocked: str = "",
        decay_spread: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pruning failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRUNING_FAILURE_PROMPT.format(
                dead_branches=dead_branches,
                resources_consumed=resources_consumed or "Not specified",
                growth_blocked=growth_blocked or "Not specified",
                decay_spread=decay_spread or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRUNING_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dead_branches": dead_branches[:200],
            "pruning_failure": data.get("pruning_failure", False),
            "severity": data.get("severity", ""),
            "resources_consumed": data.get("resources_consumed", ""),
            "growth_blocked": data.get("growth_blocked", ""),
            "decay_spread": data.get("decay_spread", ""),
            "recommendation": data.get("recommendation", ""),
        }

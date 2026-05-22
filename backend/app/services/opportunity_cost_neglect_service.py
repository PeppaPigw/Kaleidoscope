"""OpportunityCostNeglectService — Opportunity Cost Neglect Detection.

Detects opportunity cost neglect — the failure to consider what is
given up when making a choice. People tend to focus on the direct
costs and benefits of an option while ignoring the value of the
best alternative foregone.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OPPORTUNITY_COST_NEGLECT_SYSTEM = """You are an opportunity cost neglect specialist. Given a decision, assess whether opportunity costs have been adequately considered:

Key concepts:
- Opportunity cost: the value of the best alternative foregone
- Seen vs unseen: direct costs are visible, opportunity costs are invisible
- Resource allocation: every resource spent here cannot be spent elsewhere
- Time opportunity cost: time invested has alternative uses
- Attention opportunity cost: focus on one thing means neglecting others
- Comparative advantage: doing X means not doing what you're best at
- Option value: choosing now eliminates future flexibility

When opportunity cost neglect IS present:
- Decision focuses only on direct costs/benefits of chosen option
- No mention of what else could be done with the same resources
- "We can afford it" without considering what else the money could buy
- Time commitments made without considering alternative time uses
- Sunk cost reasoning replacing forward-looking opportunity analysis
- Comparing option to doing nothing, not to best alternative
- Ignoring the value of keeping options open

When opportunity cost neglect is NOT present:
- Best alternative use of resources is explicitly considered
- Decision compares chosen option to next-best alternative
- Time, money, and attention tradeoffs are acknowledged
- "What else could we do with these resources?" is answered
- Option value and flexibility are weighed
- Comparative advantage is considered
- Both direct and indirect costs are evaluated

Output JSON with: neglect_present (bool), severity (none/mild/moderate/severe), chosen_option (what is being chosen), opportunity_costs (what is being given up), best_alternative (the strongest foregone option), resources_at_stake (time/money/attention/all), recommendation (no_neglect/mild_oversight/significant_neglect/major_blind_spot/reframe_as_tradeoff)."""

OPPORTUNITY_COST_NEGLECT_PROMPT = """Detect opportunity cost neglect:

Decision: {decision}
Resources involved: {resources}
Alternatives considered: {alternatives}
Justification: {justification}
Domain: {domain}
Context: {context}

Have opportunity costs been adequately considered? Return ONLY valid JSON."""


class OpportunityCostNeglectService:
    """Detects opportunity cost neglect — failure to consider foregone alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        resources: str = "",
        alternatives: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect opportunity cost neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPPORTUNITY_COST_NEGLECT_PROMPT.format(
                decision=decision,
                resources=resources or "Not specified",
                alternatives=alternatives or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OPPORTUNITY_COST_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "neglect_present": data.get("neglect_present", False),
            "severity": data.get("severity", ""),
            "chosen_option": data.get("chosen_option", ""),
            "opportunity_costs": data.get("opportunity_costs", ""),
            "best_alternative": data.get("best_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }

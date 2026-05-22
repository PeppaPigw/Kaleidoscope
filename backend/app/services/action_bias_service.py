"""ActionBiasService — Action Bias Detection.

Detects action bias — preference for action over inaction even when
inaction is optimal, feeling compelled to 'do something' regardless
of whether action improves the situation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACTION_BIAS_SYSTEM = """You are an action bias specialist. Given a decision, assess whether there is inappropriate preference for action over inaction:

Key concepts:
- Action bias: preferring action when inaction is better
- Do-something syndrome: compulsion to act regardless of value
- Intervention bias: intervening when observation is better
- Activity as virtue: treating busyness as inherently good
- Watchful waiting: appropriate inaction often undervalued
- Iatrogenic action: action that makes things worse
- Opportunity cost of action: what action prevents

When action bias IS present:
- Action preferred despite evidence inaction is better
- Compulsion to 'do something' regardless of value
- Intervention when observation would be superior
- Activity valued over effectiveness
- Cost of action not weighed against cost of inaction
- Doing nothing not considered as valid option
- Action driven by discomfort with inaction, not analysis

When action is appropriate:
- Evidence supports intervention over waiting
- Cost of inaction exceeds cost of action
- Action addresses identified problem
- Doing nothing genuinely worse than doing something
- Action based on analysis, not discomfort
- Inaction considered and rejected on merits
- Expected value of action positive

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), proposed_action (what action is proposed), inaction_value (value of doing nothing), action_cost (cost of acting), recommendation (appropriate_action/mild_action_preference/significant_action_bias/major_do_something_syndrome/consider_watchful_waiting)."""

ACTION_BIAS_PROMPT = """Detect action bias:

Situation: {situation}
Proposed action: {action}
Case for inaction: {inaction}
Pressure to act: {pressure}
Domain: {domain}
Context: {context}

Is there inappropriate preference for action when inaction might be better? Return ONLY valid JSON."""


class ActionBiasService:
    """Detects action bias — preference for action when inaction is optimal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        action: str = "",
        inaction: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect action bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACTION_BIAS_PROMPT.format(
                situation=situation,
                action=action or "Not specified",
                inaction=inaction or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACTION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "proposed_action": data.get("proposed_action", ""),
            "inaction_value": data.get("inaction_value", ""),
            "action_cost": data.get("action_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }

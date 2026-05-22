"""StatusQuoInertiaService — Status Quo Inertia Detection.

Detects status quo inertia — the tendency to default to the current
state without adequately evaluating whether change would be
beneficial. This goes beyond simple status quo bias to include
organizational and systemic inertia that prevents rational change.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STATUS_QUO_INERTIA_SYSTEM = """You are a status quo inertia specialist. Given a decision, assess whether inertia is preventing rational evaluation of change:

Key concepts:
- Status quo bias: preference for current state regardless of merit
- Omission bias: preferring inaction over action even when action is better
- Default effect: tendency to stick with pre-selected options
- Loss aversion: changes feel like losses even when net positive
- Switching costs: real costs of change vs perceived costs
- Organizational inertia: systemic resistance to change
- Endowment effect: overvaluing what you already have

When status quo inertia IS present:
- "If it ain't broke, don't fix it" applied to suboptimal situations
- Change rejected without evaluating potential benefits
- Current state treated as neutral baseline when it has real costs
- Switching costs exaggerated relative to benefits of change
- "We've always done it this way" as justification
- Burden of proof asymmetrically placed on change
- Ignoring ongoing costs of maintaining current state

When status quo inertia is NOT present:
- Current state and alternatives evaluated on equal footing
- Switching costs realistically assessed against benefits
- Ongoing costs of status quo are acknowledged
- Change is rejected for specific, substantive reasons
- Both action and inaction risks are considered
- Default is questioned rather than assumed correct
- Decision is based on expected value, not familiarity

Output JSON with: inertia_present (bool), severity (none/mild/moderate/severe), current_state (what is being maintained), change_proposed (what change is being resisted), switching_costs (real costs of changing), ongoing_costs (costs of staying), asymmetry (how are change and status quo evaluated differently), recommendation (no_inertia/mild_preference/significant_inertia/major_stagnation/evaluate_on_merits)."""

STATUS_QUO_INERTIA_PROMPT = """Detect status quo inertia:

Decision: {decision}
Current state: {current_state}
Proposed change: {proposed_change}
Resistance reasons: {resistance}
Domain: {domain}
Context: {context}

Is inertia preventing rational evaluation of change? Return ONLY valid JSON."""


class StatusQuoInertiaService:
    """Detects status quo inertia — irrational resistance to change."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        current_state: str = "",
        proposed_change: str = "",
        resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect status quo inertia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STATUS_QUO_INERTIA_PROMPT.format(
                decision=decision,
                current_state=current_state or "Not specified",
                proposed_change=proposed_change or "Not specified",
                resistance=resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STATUS_QUO_INERTIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "inertia_present": data.get("inertia_present", False),
            "severity": data.get("severity", ""),
            "current_state": data.get("current_state", ""),
            "change_proposed": data.get("change_proposed", ""),
            "switching_costs": data.get("switching_costs", ""),
            "ongoing_costs": data.get("ongoing_costs", ""),
            "recommendation": data.get("recommendation", ""),
        }

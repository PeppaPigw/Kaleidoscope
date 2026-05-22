"""DecisionParalysisService — Decision Paralysis Detection.

Detects decision paralysis — inability to decide due to excessive
options, information overload, or fear of making the wrong choice,
leading to inaction when action is needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECISION_PARALYSIS_SYSTEM = """You are a decision paralysis specialist. Given a decision situation, assess whether paralysis is preventing needed action:

Key concepts:
- Decision paralysis: inability to choose despite need to act
- Analysis paralysis: over-analyzing preventing decision
- Choice overload: too many options preventing selection
- Perfect information seeking: waiting for certainty that won't come
- Fear of wrong choice: paralysis from anticipated regret
- Maximizer trap: seeking best option when good enough suffices
- Decision avoidance: disguising inaction as deliberation

When decision paralysis IS present:
- Decision needed but not being made
- Analysis continuing past point of diminishing returns
- Options proliferating without convergence
- Perfect information sought when unavailable
- Fear of wrong choice preventing any choice
- Deliberation disguising avoidance
- Cost of delay exceeding cost of imperfect choice

When deliberation is appropriate:
- Decision genuinely complex and high-stakes
- New information expected that would change decision
- Deliberation producing genuine insight
- Time pressure not yet critical
- Options genuinely difficult to compare
- Reversibility makes delay low-cost
- Consultation needed before deciding

Output JSON with: paralysis_present (bool), severity (none/mild/moderate/severe), decision (what decision is needed), blockers (what prevents deciding), cost_of_delay (what delay costs), good_enough (what good-enough option exists), recommendation (appropriate_deliberation/mild_overthinking/significant_paralysis/major_decision_avoidance/decide_and_iterate)."""

DECISION_PARALYSIS_PROMPT = """Detect decision paralysis:

Situation: {situation}
Decision needed: {decision}
Options: {options}
Time pressure: {pressure}
Domain: {domain}
Context: {context}

Is inability to decide preventing needed action? Return ONLY valid JSON."""


class DecisionParalysisService:
    """Detects decision paralysis — inability to decide when action is needed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        decision: str = "",
        options: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect decision paralysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DECISION_PARALYSIS_PROMPT.format(
                situation=situation,
                decision=decision or "Not specified",
                options=options or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DECISION_PARALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "paralysis_present": data.get("paralysis_present", False),
            "severity": data.get("severity", ""),
            "blockers": data.get("blockers", ""),
            "cost_of_delay": data.get("cost_of_delay", ""),
            "good_enough": data.get("good_enough", ""),
            "recommendation": data.get("recommendation", ""),
        }

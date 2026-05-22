"""GamblersConceitService — Gambler's Conceit Detection.

Detects gambler's conceit — the belief that one will be able
to stop a risky behavior while still ahead. "I'll quit while
I'm winning." Different from gambler's fallacy (which is about
probability). This is about overconfidence in future
self-control while currently engaged in rewarding behavior.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GAMBLERS_CONCEIT_SYSTEM = """You are a gambler's conceit specialist. Given a plan to stop a risky behavior "at the right time," assess whether the person is overestimating their future self-control:

Key concepts:
- Gambler's conceit: believing you'll stop while ahead
- Hot-cold empathy gap: underestimating future temptation while currently calm
- Self-control overconfidence: overestimating future willpower
- Escalation of commitment interaction: harder to stop as investment grows
- Reward momentum: success makes stopping harder, not easier
- Stopping rules: vague stopping criteria that shift with circumstances
- Present self vs. future self: assuming future self will be more disciplined

When gambler's conceit IS present:
- "I'll stop when I'm ahead" without concrete stopping criteria
- Believing future self will resist temptation current self can't
- "Just one more" repeatedly without actual stopping
- Vague exit criteria that keep shifting
- Past failures to stop not informing current confidence
- "This time I'll know when to quit"

When the stopping plan IS credible:
- Concrete, pre-committed stopping criteria exist
- External accountability mechanisms are in place
- Past behavior demonstrates ability to stop
- The stopping criteria are not easily rationalized away
- Others will enforce the stopping point
- The person has a track record of self-control in this domain

Output JSON with: gamblers_conceit_present (bool), severity (none/mild/moderate/severe), behavior (what risky behavior is being continued), stopping_plan (what is the plan to stop), stopping_criteria (how specific are the criteria?), past_stopping_success (has the person successfully stopped before?), accountability (what external accountability exists?), shifting_goalposts (bool — have criteria shifted before?), reward_momentum (is success making stopping harder?), recommendation (stopping_plan_credible/mild_overconfidence/significant_conceit/major_gamblers_conceit/pre_commit_now)."""

GAMBLERS_CONCEIT_PROMPT = """Detect gambler's conceit:

Behavior: {behavior}
Stopping plan: {plan}
Past attempts: {past}
Current state: {state}
Domain: {domain}
Context: {context}

Is the person overestimating their ability to stop while ahead? Return ONLY valid JSON."""


class GamblersConceitService:
    """Detects gambler's conceit — overconfidence in ability to stop while ahead."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        behavior: str,
        *,
        plan: str = "",
        past: str = "",
        state: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect gambler's conceit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GAMBLERS_CONCEIT_PROMPT.format(
                behavior=behavior,
                plan=plan or "Not specified",
                past=past or "Not specified",
                state=state or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GAMBLERS_CONCEIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "behavior": behavior[:200],
            "gamblers_conceit_present": data.get("gamblers_conceit_present", False),
            "severity": data.get("severity", ""),
            "stopping_plan": data.get("stopping_plan", ""),
            "stopping_criteria": data.get("stopping_criteria", ""),
            "past_stopping_success": data.get("past_stopping_success", ""),
            "accountability": data.get("accountability", ""),
            "shifting_goalposts": data.get("shifting_goalposts", False),
            "reward_momentum": data.get("reward_momentum", ""),
            "recommendation": data.get("recommendation", ""),
        }

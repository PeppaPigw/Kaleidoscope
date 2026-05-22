"""EscalationOfCommitmentService — Escalation of Commitment Detection.

Detects escalation of commitment (irrational escalation) — continuing
a failing course of action because of prior investment, ego, or
inability to accept loss. "Throwing good money after bad." Staw (1976).
Combines sunk cost fallacy with self-justification, social pressure,
and completion bias.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ESCALATION_SYSTEM = """You are an escalation of commitment specialist. Given a decision to continue or abandon a course of action, assess whether irrational escalation is occurring:

Key drivers of escalation:
- Sunk cost effect: prior investment makes abandonment feel wasteful
- Self-justification: admitting failure threatens self-image
- Social pressure: others are watching; abandonment = public failure
- Completion bias: desire to finish what was started regardless of value
- Selective perception: noticing confirming signals, ignoring disconfirming
- Prospect theory: in the domain of losses, people become risk-seeking
- Organizational momentum: bureaucratic inertia keeps projects alive

Warning signs:
- Increasing investment despite declining returns
- Moving goalposts: redefining success to match current trajectory
- Ignoring negative feedback or kill criteria
- "We've come too far to stop now"
- Comparing to sunk costs rather than future expected value

Output JSON with: escalation_present (bool), severity (none/mild/moderate/severe/extreme), course_of_action (what is being continued), total_invested (what has been sunk so far), future_expected_value (rational assessment of continuing), abandonment_value (what could be gained by stopping and redirecting), escalation_drivers (which psychological/social factors are driving continuation), sunk_cost_magnitude (how large the sunk investment is), self_justification_pressure (0-1 — how much ego is invested), social_pressure_to_continue (0-1 — how much face would be lost by stopping), completion_bias (0-1 — how much "almost done" feeling drives continuation), kill_criteria_exist (bool — are there defined conditions for stopping?), kill_criteria_met (bool — have those conditions been met?), goalposts_moved (bool — has success been redefined?), negative_feedback_ignored (what warning signs are being dismissed), rational_decision (continue/pivot/abandon based on future value only), who_benefits_from_continuation (who gains from not stopping), recommendation (continuation_justified/mild_escalation/significant_escalation/irrational_continuation/immediate_reassessment_needed)."""

ESCALATION_PROMPT = """Detect escalation of commitment:

Situation: {situation}
Investment so far: {investment}
Current results: {results}
Reasons to continue: {reasons_continue}
Domain: {domain}
Context: {context}

Is irrational escalation occurring? Return ONLY valid JSON."""


class EscalationOfCommitmentService:
    """Detects escalation of commitment — irrational continuation of failing courses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        investment: str = "",
        results: str = "",
        reasons_continue: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect escalation of commitment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ESCALATION_PROMPT.format(
                situation=situation,
                investment=investment or "Not specified",
                results=results or "Not specified",
                reasons_continue=reasons_continue or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ESCALATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "escalation_present": data.get("escalation_present", False),
            "severity": data.get("severity", ""),
            "course_of_action": data.get("course_of_action", ""),
            "total_invested": data.get("total_invested", ""),
            "future_expected_value": data.get("future_expected_value", ""),
            "abandonment_value": data.get("abandonment_value", ""),
            "escalation_drivers": data.get("escalation_drivers", []),
            "sunk_cost_magnitude": data.get("sunk_cost_magnitude", ""),
            "self_justification_pressure": data.get("self_justification_pressure", 0),
            "social_pressure_to_continue": data.get("social_pressure_to_continue", 0),
            "completion_bias": data.get("completion_bias", 0),
            "kill_criteria_exist": data.get("kill_criteria_exist", False),
            "kill_criteria_met": data.get("kill_criteria_met", False),
            "goalposts_moved": data.get("goalposts_moved", False),
            "negative_feedback_ignored": data.get("negative_feedback_ignored", ""),
            "rational_decision": data.get("rational_decision", ""),
            "who_benefits_from_continuation": data.get("who_benefits_from_continuation", ""),
            "recommendation": data.get("recommendation", ""),
        }

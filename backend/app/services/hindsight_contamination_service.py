"""HindsightContaminationService — Hindsight Contamination Detection.

Detects hindsight contamination — when knowledge of outcomes
contaminates the assessment of prior decisions. Once we know
what happened, we can't fairly evaluate whether the decision
was reasonable given what was known at the time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HINDSIGHT_CONTAMINATION_SYSTEM = """You are a hindsight contamination specialist. Given an assessment of a past decision, determine whether outcome knowledge is contaminating the evaluation:

Key concepts:
- Hindsight contamination: outcome knowledge biasing decision evaluation
- Creeping determinism: past events seem inevitable after the fact
- Outcome bias: judging decisions by results rather than process
- Knew-it-all-along effect: believing the outcome was predictable
- Process vs outcome: good decisions can have bad outcomes and vice versa
- Information available: what was knowable at decision time
- Counterfactual thinking: what could have been known vs what was known

When hindsight contamination IS present:
- Decision judged by outcome rather than process
- "They should have known" when information wasn't available
- Outcome treated as if it was predictable
- Decision-maker blamed for not foreseeing unforeseeable events
- Alternative outcomes not considered in evaluation
- "Obviously" applied to something that wasn't obvious at the time
- Information available after the decision used to judge the decision

When hindsight contamination is NOT present:
- Decision evaluated based on information available at the time
- Process quality assessed independently of outcome
- Uncertainty at decision time acknowledged
- Good decisions with bad outcomes recognized as good decisions
- Evaluation considers what was knowable, not what is known now
- Alternative outcomes acknowledged as having been possible
- Distinction made between decision quality and outcome quality

Output JSON with: contamination_present (bool), severity (none/mild/moderate/severe), decision (what decision is being evaluated), outcome_known (what outcome is known), information_at_time (what was knowable when decided), hindsight_claim (what is being claimed with hindsight), recommendation (no_contamination/mild_outcome_bias/significant_contamination/major_hindsight_distortion/evaluate_with_decision_time_info)."""

HINDSIGHT_CONTAMINATION_PROMPT = """Detect hindsight contamination:

Assessment: {assessment}
Decision evaluated: {decision}
Outcome: {outcome}
Information at time: {info_at_time}
Domain: {domain}
Context: {context}

Is knowledge of the outcome contaminating the evaluation of this decision? Return ONLY valid JSON."""


class HindsightContaminationService:
    """Detects hindsight contamination — outcome knowledge biasing decision evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        decision: str = "",
        outcome: str = "",
        info_at_time: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hindsight contamination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HINDSIGHT_CONTAMINATION_PROMPT.format(
                assessment=assessment,
                decision=decision or "Not specified",
                outcome=outcome or "Not specified",
                info_at_time=info_at_time or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HINDSIGHT_CONTAMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "contamination_present": data.get("contamination_present", False),
            "severity": data.get("severity", ""),
            "outcome_known": data.get("outcome_known", ""),
            "information_at_time": data.get("information_at_time", ""),
            "hindsight_claim": data.get("hindsight_claim", ""),
            "recommendation": data.get("recommendation", ""),
        }

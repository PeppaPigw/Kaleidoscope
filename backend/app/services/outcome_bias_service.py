"""OutcomeBiasService — Outcome Bias Detection.

Detects outcome bias — judging the quality of a decision by its
outcome rather than by the quality of the decision process at
the time it was made. Baron & Hershey (1988). A good decision
can have a bad outcome (bad luck) and a bad decision can have
a good outcome (good luck). Confusing outcome quality with
decision quality leads to wrong lessons learned.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OUTCOME_SYSTEM = """You are an outcome bias specialist. Given a judgment about a past decision, assess whether the outcome is inappropriately influencing the evaluation of the decision process:

Key concepts (Baron & Hershey, 1988):
- Outcome bias: judging decisions by results rather than process quality
- Process vs. outcome: a good process can yield bad results and vice versa
- Resulting: poker term for judging a play by whether it won rather than expected value
- Hindsight bias overlap: knowing the outcome makes the "right" choice seem obvious
- Survivorship bias overlap: only seeing successful outcomes of risky decisions
- Moral luck: judging moral responsibility based on outcomes rather than intentions

When outcome bias IS present:
- Praising a risky decision because it happened to work out
- Condemning a sound decision because of an unlikely bad outcome
- "It worked, so it was the right call" (ignoring expected value)
- Firing someone for a decision that was correct given available information
- Learning wrong lessons from lucky successes or unlucky failures
- Confusing "it turned out well" with "it was well-reasoned"

When outcome-based judgment IS appropriate:
- The outcome reveals information that was knowable at decision time
- A pattern of bad outcomes suggests systematic process failure
- The decision-maker ignored available information that predicted the outcome
- The outcome was the most likely result of the decision (not luck)
- Process evaluation has already been done and outcome adds signal

Output JSON with: outcome_bias_present (bool), severity (none/mild/moderate/severe), decision (what decision is being evaluated), outcome (what happened), process_quality (how good was the decision process at the time?), information_available (what was known when the decision was made), outcome_predictability (was this outcome likely or unlikely given the decision?), luck_factor (how much did luck contribute to the outcome?), correct_lesson (what should actually be learned), wrong_lesson (what lesson is being drawn from the outcome), pattern_vs_instance (is this one case or a pattern?), counterfactual (what would have happened with the alternative?), recommendation (outcome_informative/mild_outcome_bias/significant_outcome_bias/major_resulting/evaluate_process_not_outcome)."""

OUTCOME_PROMPT = """Detect outcome bias:

Decision evaluated: {decision}
Outcome: {outcome}
Judgment being made: {judgment}
Information at time: {information}
Domain: {domain}
Context: {context}

Is the outcome inappropriately influencing evaluation of the decision? Return ONLY valid JSON."""


class OutcomeBiasService:
    """Detects outcome bias — judging decisions by results rather than process."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        outcome: str = "",
        judgment: str = "",
        information: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect outcome bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OUTCOME_PROMPT.format(
                decision=decision,
                outcome=outcome or "Not specified",
                judgment=judgment or "Not specified",
                information=information or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OUTCOME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "outcome_bias_present": data.get("outcome_bias_present", False),
            "severity": data.get("severity", ""),
            "outcome": data.get("outcome", ""),
            "process_quality": data.get("process_quality", ""),
            "information_available": data.get("information_available", ""),
            "outcome_predictability": data.get("outcome_predictability", ""),
            "luck_factor": data.get("luck_factor", ""),
            "correct_lesson": data.get("correct_lesson", ""),
            "wrong_lesson": data.get("wrong_lesson", ""),
            "pattern_vs_instance": data.get("pattern_vs_instance", ""),
            "counterfactual": data.get("counterfactual", ""),
            "recommendation": data.get("recommendation", ""),
        }

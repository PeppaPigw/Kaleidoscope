"""PseudocertaintyService — Pseudocertainty Effect Detection.

Detects pseudocertainty effect — tendency to perceive an outcome
as certain while it is actually uncertain, particularly in
multi-stage decisions. Tversky & Kahneman (1981). When a
gamble is framed as sequential stages, people treat conditional
probabilities as certainties. "If I pass stage 1, I definitely
get X" ignoring that stage 1 itself is uncertain.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PSEUDOCERTAINTY_SYSTEM = """You are a pseudocertainty effect specialist. Given a multi-stage decision or conditional outcome, assess whether someone is treating uncertain outcomes as certain:

Key concepts (Tversky & Kahneman, 1981):
- Pseudocertainty: treating conditional outcomes as certain
- Multi-stage framing: breaking decisions into stages creates illusion of certainty
- Certainty effect interaction: overweighting outcomes perceived as certain
- Conditional probability neglect: ignoring that earlier conditions may not hold
- Sequential framing: same gamble framed as stages vs single choice
- Risk elimination illusion: believing risk is eliminated when it's merely conditional
- Insurance framing: feeling fully protected when coverage is conditional

When pseudocertainty IS present:
- "Once I get past X, I'm guaranteed Y" (when X is uncertain)
- Multi-stage plans where each stage is treated as certain
- Conditional guarantees treated as absolute guarantees
- "If the market goes up, I'll definitely profit" (ignoring the if)
- Insurance that covers only specific scenarios treated as full coverage
- Sequential decisions where early uncertainty is ignored

When the certainty IS genuine:
- The conditional probability is genuinely 1.0
- The person correctly accounts for all stages of uncertainty
- The framing accurately represents the decision structure
- Earlier conditions are already satisfied
- The person explicitly acknowledges the conditionality

Output JSON with: pseudocertainty_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), perceived_certainty (what is perceived as certain), actual_probability (what is the actual probability), conditional_on (what condition must hold), condition_probability (probability of the condition), framing (how is the decision framed), overall_probability (true probability considering all stages), recommendation (certainty_genuine/mild_pseudocertainty/significant_conditional_neglect/major_pseudocertainty/compute_joint_probability)."""

PSEUDOCERTAINTY_PROMPT = """Detect pseudocertainty effect:

Decision: {decision}
Perceived outcome: {perceived}
Conditions: {conditions}
Stages: {stages}
Domain: {domain}
Context: {context}

Is someone treating a conditional/uncertain outcome as certain? Return ONLY valid JSON."""


class PseudocertaintyService:
    """Detects pseudocertainty effect — treating conditional outcomes as certain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        perceived: str = "",
        conditions: str = "",
        stages: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect pseudocertainty effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PSEUDOCERTAINTY_PROMPT.format(
                decision=decision,
                perceived=perceived or "Not specified",
                conditions=conditions or "Not specified",
                stages=stages or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PSEUDOCERTAINTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "pseudocertainty_present": data.get("pseudocertainty_present", False),
            "severity": data.get("severity", ""),
            "perceived_certainty": data.get("perceived_certainty", ""),
            "actual_probability": data.get("actual_probability", ""),
            "conditional_on": data.get("conditional_on", ""),
            "condition_probability": data.get("condition_probability", ""),
            "framing": data.get("framing", ""),
            "overall_probability": data.get("overall_probability", ""),
            "recommendation": data.get("recommendation", ""),
        }

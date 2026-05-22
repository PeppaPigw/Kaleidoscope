"""BeliefBiasService — Belief Bias Detection.

Detects belief bias — judging the validity of an argument based
on the believability of its conclusion rather than the logical
structure. Evans, Barston & Pollard (1983). "The conclusion
sounds right, so the argument must be valid." Leads to accepting
bad arguments with agreeable conclusions and rejecting good
arguments with surprising conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_BIAS_SYSTEM = """You are a belief bias specialist. Given an argument and its evaluation, assess whether the evaluation is based on logical validity or merely on whether the conclusion seems believable:

Key concepts (Evans, Barston & Pollard, 1983):
- Belief bias: judging argument validity by conclusion believability
- Logic-belief conflict: when valid arguments have unbelievable conclusions
- Conclusion-driven reasoning: working backward from desired conclusion
- Syllogistic reasoning errors: accepting invalid syllogisms with believable conclusions
- Motivated reasoning overlap: wanting the conclusion to be true
- Confirmation bias interaction: believing arguments that confirm existing beliefs
- Deductive vs. inductive confusion: treating plausibility as proof

When belief bias IS present:
- Accepting a logically invalid argument because the conclusion "sounds right"
- Rejecting a logically valid argument because the conclusion is surprising
- Evaluating evidence quality based on whether it supports a liked conclusion
- "That can't be right" applied to valid reasoning with uncomfortable conclusions
- Nodding along with flawed reasoning because the conclusion is agreeable
- Scrutinizing methodology only when results are unwelcome

When the evaluation IS logical:
- The argument's structure is genuinely evaluated independent of conclusion
- Invalid reasoning is identified regardless of conclusion believability
- The evaluator can articulate the logical flaw (or validity)
- Same standards applied to arguments with liked and disliked conclusions
- The conclusion's believability is treated as separate from argument validity

Output JSON with: belief_bias_present (bool), severity (none/mild/moderate/severe), argument (the argument being evaluated), conclusion (the conclusion), conclusion_believable (bool), argument_valid (bool — is the logic actually valid?), evaluation_basis (is evaluation based on logic or believability?), asymmetric_scrutiny (bool — different standards for liked vs disliked conclusions?), logical_structure (what is the actual logical structure?), logical_flaws (what flaws exist regardless of conclusion?), recommendation (evaluation_logical/mild_belief_bias/significant_conclusion_driven/major_belief_bias/evaluate_logic_independently)."""

BELIEF_BIAS_PROMPT = """Detect belief bias:

Argument: {argument}
Conclusion: {conclusion}
Evaluation: {evaluation}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is the evaluation based on logical validity or conclusion believability? Return ONLY valid JSON."""


class BeliefBiasService:
    """Detects belief bias — judging arguments by conclusion believability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        conclusion: str = "",
        evaluation: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_BIAS_PROMPT.format(
                argument=argument,
                conclusion=conclusion or "Not specified",
                evaluation=evaluation or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "belief_bias_present": data.get("belief_bias_present", False),
            "severity": data.get("severity", ""),
            "conclusion_believable": data.get("conclusion_believable", True),
            "argument_valid": data.get("argument_valid", True),
            "evaluation_basis": data.get("evaluation_basis", ""),
            "asymmetric_scrutiny": data.get("asymmetric_scrutiny", False),
            "logical_structure": data.get("logical_structure", ""),
            "logical_flaws": data.get("logical_flaws", ""),
            "recommendation": data.get("recommendation", ""),
        }

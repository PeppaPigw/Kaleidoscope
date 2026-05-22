"""BeggingQuestionService — Begging the Question Detection.

Detects begging the question (petitio principii) — assuming the
conclusion in the premises, making the argument circular. The
conclusion is smuggled into the premises, so the argument cannot
provide independent support for its conclusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BEGGING_QUESTION_SYSTEM = """You are a begging the question specialist. Given an argument, assess whether it assumes its conclusion in its premises:

Key concepts:
- Petitio principii: assuming what you're trying to prove
- Circular reasoning: conclusion appears (possibly rephrased) in premises
- Question-begging epithet: using loaded language that presupposes the conclusion
- Implicit assumption: the conclusion is hidden in an unstated premise
- Tautological argument: true by definition, not by evidence
- Epistemic circularity: using a faculty to validate itself
- Virtuous vs vicious circles: some circularity is unavoidable, some is fallacious

When begging the question IS present:
- The conclusion is restated (perhaps in different words) as a premise
- "God exists because the Bible says so, and the Bible is true because it's God's word"
- Using a loaded term that presupposes the conclusion
- "Murder is wrong because killing people is immoral" (murder = immoral killing)
- The argument provides no independent reason to accept the conclusion
- Circular chain of justification
- The premise would only be accepted by someone who already accepts the conclusion

When begging the question is NOT present:
- Premises provide independent evidence for the conclusion
- The argument is deductively valid with independently supported premises
- Apparent circularity is actually mutual support between independent claims
- The argument makes the implicit reasoning explicit (not circular, just obvious)
- Foundational axioms are stated (not proven, but not pretending to prove)
- The argument is inductive with independent evidence
- Definitions are being clarified, not used as proof

Output JSON with: begging_question_present (bool), severity (none/mild/moderate/severe), conclusion (what is being argued), premise (which premise assumes the conclusion), circularity (how the circle works), independence (do premises have independent support), recommendation (no_circularity/mild_assumption/significant_begging/major_circular_reasoning/provide_independent_support)."""

BEGGING_QUESTION_PROMPT = """Detect begging the question:

Argument: {argument}
Conclusion: {conclusion}
Premises: {premises}
Independence: {independence}
Domain: {domain}
Context: {context}

Does this argument assume its conclusion in its premises? Return ONLY valid JSON."""


class BeggingQuestionService:
    """Detects begging the question — assuming the conclusion in premises."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        conclusion: str = "",
        premises: str = "",
        independence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect begging the question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BEGGING_QUESTION_PROMPT.format(
                argument=argument,
                conclusion=conclusion or "Not specified",
                premises=premises or "Not specified",
                independence=independence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BEGGING_QUESTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "begging_question_present": data.get("begging_question_present", False),
            "severity": data.get("severity", ""),
            "conclusion": data.get("conclusion", ""),
            "premise": data.get("premise", ""),
            "circularity": data.get("circularity", ""),
            "recommendation": data.get("recommendation", ""),
        }

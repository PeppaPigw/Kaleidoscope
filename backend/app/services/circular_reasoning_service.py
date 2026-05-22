"""CircularReasoningService — Circular Reasoning Detection.

Detects circular reasoning — using the conclusion as a premise
in a chain of reasoning that may be longer and less obvious than
simple begging the question. The circularity may span multiple
steps, making it harder to detect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CIRCULAR_REASONING_SYSTEM = """You are a circular reasoning specialist. Given an argument chain, assess whether it contains circular logic:

Key concepts:
- Circular reasoning: conclusion appears (possibly transformed) in premises
- Indirect circularity: A proves B proves C proves A
- Definitional circularity: defining X in terms of Y and Y in terms of X
- Epistemic circularity: using a faculty to validate itself
- Coherentism vs foundationalism: some circularity may be acceptable
- Virtuous circles: mutual support vs vicious circles: no independent support
- Hidden circularity: the circle may be disguised by rephrasing

When circular reasoning IS present:
- A → B → C → A (the chain loops back)
- Defining terms in terms of each other without independent grounding
- "X is true because Y, and Y is true because X"
- Using a rephrased version of the conclusion as evidence
- Justifying a method by its own results
- "The Bible is true because God wrote it; God exists because the Bible says so"
- Long chains that ultimately loop back to their starting point

When circular reasoning is NOT present:
- Mutual support between independently grounded claims
- Iterative refinement (each pass adds new information)
- Coherence arguments that acknowledge their structure
- Feedback loops in systems (not logical arguments)
- Claims that happen to support each other but have independent evidence
- Spiral reasoning: returning to a topic with new information
- Bootstrapping with acknowledged limitations

Output JSON with: circular_reasoning_present (bool), severity (none/mild/moderate/severe), chain (the reasoning chain), loop_point (where it circles back), chain_length (how many steps in the circle), independent_support (do any premises have independent support), recommendation (no_circularity/mild_mutual_dependence/significant_circular_reasoning/major_logical_circle/provide_independent_support)."""

CIRCULAR_REASONING_PROMPT = """Detect circular reasoning:

Argument: {argument}
Reasoning chain: {chain}
Conclusion: {conclusion}
Support offered: {support}
Domain: {domain}
Context: {context}

Does this reasoning chain contain circular logic? Return ONLY valid JSON."""


class CircularReasoningService:
    """Detects circular reasoning — conclusion used as premise in a chain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        chain: str = "",
        conclusion: str = "",
        support: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect circular reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CIRCULAR_REASONING_PROMPT.format(
                argument=argument,
                chain=chain or "Not specified",
                conclusion=conclusion or "Not specified",
                support=support or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CIRCULAR_REASONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "circular_reasoning_present": data.get("circular_reasoning_present", False),
            "severity": data.get("severity", ""),
            "chain": data.get("chain", ""),
            "loop_point": data.get("loop_point", ""),
            "independent_support": data.get("independent_support", ""),
            "recommendation": data.get("recommendation", ""),
        }

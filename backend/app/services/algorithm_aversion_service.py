"""AlgorithmAversionService — Algorithm Aversion Detection.

Detects algorithm aversion — preferring human judgment over
algorithmic/statistical methods even when algorithms demonstrably
outperform humans. Dietvorst, Simmons & Massey (2015). People
abandon algorithms after seeing them err once, even though
humans err more frequently. Imperfect algorithms are rejected
while imperfect humans are tolerated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ALGORITHM_AVERSION_SYSTEM = """You are an algorithm aversion specialist. Given a decision about whether to use algorithmic vs human judgment, assess whether algorithm aversion is present:

Key concepts (Dietvorst, Simmons & Massey, 2015):
- Algorithm aversion: preferring humans over better-performing algorithms
- Perfection standard: algorithms held to higher standard than humans
- Error intolerance: one algorithmic error causes abandonment
- Illusion of understanding: human reasoning feels more transparent
- Control preference: wanting human in the loop regardless of accuracy
- Uniqueness neglect: "my case is special, algorithms can't handle it"
- Accountability preference: wanting someone to blame

When algorithm aversion IS present:
- Rejecting a model that outperforms human judgment
- "I don't trust the algorithm" without evidence of poor performance
- Abandoning a tool after one error while tolerating human errors
- Preferring gut feeling over validated statistical methods
- "Every case is unique" when base rates are highly predictive
- Demanding perfection from algorithms but not from humans
- "I want a human to make this decision" when humans do worse

When human preference IS justified:
- The algorithm genuinely performs worse in this specific context
- The decision requires values/ethics that algorithms can't encode
- The algorithm has known biases in this domain
- Accountability and explainability are legally required
- The situation is genuinely novel and outside training distribution
- Human judgment adds genuine value beyond what the algorithm captures

Output JSON with: algorithm_aversion_present (bool), severity (none/mild/moderate/severe), decision (what decision method is being chosen), algorithm_performance (how well does the algorithm perform), human_performance (how well do humans perform), rejection_reason (why is the algorithm being rejected), double_standard (is a different standard applied to algorithm vs human), error_tolerance (is one algorithmic error causing rejection), recommendation (human_preference_justified/mild_algorithm_skepticism/significant_algorithm_aversion/major_performance_sacrifice/use_algorithm_with_human_oversight)."""

ALGORITHM_AVERSION_PROMPT = """Detect algorithm aversion:

Decision: {decision}
Algorithm option: {algorithm}
Human option: {human}
Rejection reason: {rejection}
Domain: {domain}
Context: {context}

Is human judgment being preferred over a better-performing algorithm without justification? Return ONLY valid JSON."""


class AlgorithmAversionService:
    """Detects algorithm aversion — preferring humans over better-performing algorithms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        algorithm: str = "",
        human: str = "",
        rejection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect algorithm aversion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ALGORITHM_AVERSION_PROMPT.format(
                decision=decision,
                algorithm=algorithm or "Not specified",
                human=human or "Not specified",
                rejection=rejection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ALGORITHM_AVERSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "algorithm_aversion_present": data.get("algorithm_aversion_present", False),
            "severity": data.get("severity", ""),
            "algorithm_performance": data.get("algorithm_performance", ""),
            "human_performance": data.get("human_performance", ""),
            "rejection_reason": data.get("rejection_reason", ""),
            "double_standard": data.get("double_standard", ""),
            "error_tolerance": data.get("error_tolerance", ""),
            "recommendation": data.get("recommendation", ""),
        }
